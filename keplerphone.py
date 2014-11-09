import pretty_midi
import librosa

import kplr

import scipy.signal
import numpy as np

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import prettyplotlib as ppl
mpl.rc('text', color='w')
mpl.rc('xtick', color='w')
mpl.rc('ytick', color='w')
mpl.rc('axes', edgecolor='w')

SCALES = {  'Blues': [0, 3, 5, 6, 7, 10],
            'Jazz Minor': [0, 2, 3, 5, 7, 9, 11],
            'Pentatonic': [0, 2, 5, 7, 9],
            'Chromatic': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'Major': [0, 2, 4, 5, 7, 9, 11],
            'Minor': [0, 2, 3, 5, 7, 9, 10],
            'Purvi': [0, 1, 4, 6, 9, 11],
            'Todi': [0, 1, 3, 6, 7, 8, 10],
            'Bhairav': [0, 1, 4, 5, 7, 8, 11],
            'Bhairavi': [0, 1, 3, 5, 7, 8, 10],
            'Kafi': [0, 2, 3, 5, 7, 9, 10],
            'Not Exactly Todi': [0, 1, 4, 6, 7, 8, 11],
            'Whole Tone': [0, 2, 4, 6, 8, 10],
            'Octatonic': [0, 2, 3, 5, 6, 8, 9, 11],

}

INSTRUMENTS = ['Overdriven guitar', 'Bag pipe', 'Ocarina']
DRUMS       = ['Splash cymbal', 'Bass drum 1', 'Acoustic snare']

BASE_DURATION = 30.0


def get_light_curves(kic):

    client = kplr.API()

    # Get the star object
    star = client.star(kic)

    # Get a list of light curve datasets.
    lcs = star.get_light_curves(short_cadence=False)

    time, flux = [], []
    for lc in lcs:
        with lc.open() as f:
            # The lightcurve data are in the first FITS HDU.
            hdu_data = f[1].data

            time.append(hdu_data["time"])
            flux.append(hdu_data["sap_flux"])

            idx = np.isfinite(time[-1]) & np.isfinite(flux[-1])
            time[-1] = time[-1][idx]
            flux[-1] = flux[-1][idx]

            if time[-1].max() - time[-1].min() < 70.0:
                time.pop(-1)
                flux.pop(-1)
    return time, flux


def get_spikes(flux, w=15):

    mf = scipy.signal.medfilt(-flux, kernel_size=w)

    mf[mf == 0] = 1.0

    z = flux / mf

    thresh = np.median(z)

    z[z < thresh] = thresh
    z = z - z.min()
    z = z / z.max()

    return z


def get_contour(flux, w=15):

    # eject the spikes
    f_filt = scipy.signal.medfilt(flux, kernel_size=w)

    f_filt = scipy.signal.detrend(f_filt)
    f_filt = f_filt - f_filt.min()
    f_filt = f_filt / f_filt.max()
    return f_filt


def quantize_contour(flux, n_scale_tones=6, n_octaves=4):

    n_bins = n_scale_tones * n_octaves

    quantiles = scipy.stats.mstats.mquantiles(flux,
                                              prob=np.linspace(0, 1., n_bins,
                                                               endpoint=False))

    z1 = np.greater.outer(quantiles, flux)

    return np.argmax(z1, axis=0)


def sustain_tones(intervals, qflux):

    changes = np.argwhere(qflux[:-1] != qflux[1:]).flatten()
    changes = np.concatenate([[0], changes])

    int_out = []
    flux_out = []

    for s, t in zip(changes[:-1], changes[1:]):
        int_out.append((intervals[s][0], intervals[t][0]))
        flux_out.append(qflux[s])

    return int_out, flux_out


def make_midi(time, flux, scale, duration,
              n_octaves=4, time_offset=0.0, note_min=48,
              lead_name='Distortion guitar',
              drum_name='Splash cymbal',
              midi_obj=None):

    if midi_obj is None:
        midi_obj = pretty_midi.PrettyMIDI()

    # Pick a voice
    program = pretty_midi.instrument_name_to_program(lead_name)
    inst = pretty_midi.Instrument(program=program)

    # Quantize the flux
    qflux = quantize_contour(get_contour(flux),
                             n_scale_tones=len(scale),
                             n_octaves=n_octaves)

    tones = note_min + np.add.outer(12 * np.arange(n_octaves), scale).ravel()

    # Iterate over note names, which will be converted to note number later
    time = time - time.min()

    time_scale = duration / float(time.max())

    time = time * time_scale + time_offset
    intervals = zip(time[:-1], time[1:])

    for t, note_t in zip(*sustain_tones(intervals, qflux)):

        # These are the zeros, skip them
        if note_t == note_min:
            continue

        # Create a Note instance for this note
        note = pretty_midi.Note(velocity=100,
                                pitch=tones[note_t],
                                start=t[0],
                                end=t[1])

        # Add it to our cello instrument
        inst.notes.append(note)

    # Add the cello instrument to the PrettyMIDI object
    midi_obj.instruments.append(inst)

    # Now do the percussion
    drum_beats = get_spikes(flux)
    program = 20
    note_t = pretty_midi.drum_name_to_note_number(drum_name)

    good_idx = librosa.peak_pick(drum_beats, 3, 3, 5, 5, 0.5, 10)

    inst = pretty_midi.Instrument(20, is_drum=True)

    for i in good_idx:
        t = intervals[i]
        note = pretty_midi.Note(velocity=100,
                                pitch=note_t,
                                start=t[0],
                                end=t[1])

        # Add it to our cello instrument
        inst.notes.append(note)

    midi_obj.instruments.append(inst)

    return midi_obj

def make_image(kic):

    output_name = os.path.join('.', 'data',
                               os.extsep.join(['{:d}'.format(kic), 'png']))

    output_name = os.path.abspath(output_name)

    if os.path.exists(output_name):
        return output_name

    time, flux = get_light_curves(kic)

    plt.figure()

    for t, f in zip(time, flux):
        idx = np.isfinite(f) & np.isfinite(t)
        ppl.plot(t[idx], f[idx])

    plt.title('kic=%d' % kic)
    plt.xlabel('Time', color='w')
    plt.ylabel('Flux', color='w')
    plt.axis('tight')

    plt.tight_layout()

    try:
        os.makedirs(os.path.dirname(output_name))
    except:
        pass

    plt.savefig(output_name, transparent=True)

    return output_name


def make_music(kic, scale='Kafi', speed=2.0):

    my_duration = (12.0 - speed) * BASE_DURATION

    output_name = os.path.join('.', 'data',
                               os.extsep.join(['{:d}-{:s}-{:.3e}'.format(kic, 
                                                                         scale,
                                                                         12.0 - speed),
                                               'mid']))

    output_name = os.path.abspath(output_name)

    if os.path.exists(output_name):
        return output_name

    time, flux = get_light_curves(kic)

    midi_obj = pretty_midi.PrettyMIDI()

    my_scale = SCALES[scale]

    for i in range(4):
        midi_obj = make_midi(time[i], flux[i], my_scale,
                             my_duration,
                             n_octaves=3, note_min=48,
                             lead_name=INSTRUMENTS[0],
                             drum_name=DRUMS[0],
                             midi_obj=midi_obj, time_offset=i * my_duration)

        midi_obj = make_midi(time[i+1], flux[i+1], [b + 7 for b in my_scale],
                             my_duration,
                             n_octaves=2, note_min=12,
                             lead_name=INSTRUMENTS[1],
                             drum_name=DRUMS[1],
                             midi_obj=midi_obj, time_offset=i * my_duration)

        midi_obj = make_midi(time[i+1], flux[i+1], [b + 7 for b in my_scale],
                             my_duration,
                             n_octaves=2, note_min=36,
                             lead_name=INSTRUMENTS[2],
                             drum_name=DRUMS[2],
                             midi_obj=midi_obj, time_offset=i * my_duration)

    try:
        os.makedirs(os.path.dirname(output_name))
    except:
        pass

    midi_obj.write(output_name)

    return output_name


def get_scales():

    return sorted(SCALES.keys())


def get_ids():

    client = kplr.API()

    kois = client.kois(where="koi_period<3", sort="koi_period")[:20]

    objs = [{'id': k.kepid, 'name': k.kepoi_name} for k in kois]

    return objs
