import pretty_midi
import librosa

import kplr

import scipy.signal
import numpy as np

SCALES = {  'blues': [0, 3, 5, 6, 7, 10],
            'jazz_minor': [0, 2, 3, 5, 7, 9, 11],
            'marwa': [0, 1, 4, 6, 9, 11],
            'todi': [0, 1, 4, 6, 7, 8, 11],
            'pentatonic': [0, 2, 5, 7, 9],
}

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


def clean_flux(f_orig, aggregate=np.median):
    
    f = f_orig.copy()
    f[~np.isfinite(f)] = aggregate(f[np.isfinite(f)])
    
    return f


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
                                              prob=np.linspace(0, 1.0, n_bins, endpoint=False))
    
    z1 = np.greater.outer(quantiles, flux)
    
    return np.argmax(z1, axis=0)


def sustain_tones(intervals, qflux):
    
    dflux = np.diff(qflux)
    
    changes = np.argwhere(qflux[:-1] != qflux[1:]).flatten()
    
    changes = np.concatenate([[0], changes])
    
    int_out = []
    flux_out = []
    
    for s, t in zip(changes[:-1], changes[1:]):
        int_out.append( (intervals[s][0], intervals[t][0] ) )
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
        # Retrieve the MIDI note number for this note name
        #note_number = pretty_midi.note_name_to_number(note_name)
        
        # These are the zeros, skip them
        if note_t == note_min:
            continue
            
        tones[note_t]

        # Create a Note instance for this note, starting at 0s and ending at .5s
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


# kic = 4912991
# kic = 12351927
#kic = 6805414
#kic = 3644071

def make_music(kic, duration=90.0, my_scale='jazz_minor'):
    
    time, flux = get_light_curves(kic)

    midi_obj = pretty_midi.PrettyMIDI()

    for i in range(4):
        midi_obj = make_midi(time[i], flux[i], my_scale,
                             duration, 
                             n_octaves=3, note_min=48, 
                             lead_name='Overdriven guitar',
                             drum_name='Splash cymbal',
                             midi_obj=midi_obj, time_offset=i * duration)

        midi_obj = make_midi(time[i+1], flux[i+1], [b + 7 for b in my_scale], 
                             duration, 
                             n_octaves=3, note_min=24, 
                             lead_name='SynthStrings 2',
                             drum_name='Bass drum 1',
                             midi_obj=midi_obj, time_offset=i * duration)
    
        midi_obj = make_midi(time[i+1], flux[i+1], [b + 5 for b in my_scale], 
                             duration, 
                             n_octaves=2, note_min=36,
                             lead_name='SynthStrings 1',
                             drum_name='Acoustic snare',
                             midi_obj=midi_obj, time_offset=i*duration)
 
    audio_data = midi_obj.fluidsynth(fs=22050,
                                     sf2_path='/usr/share/sounds/sf2/FluidR3_GM.sf2')

    # Save the audio as mp3 and spit it back

    pass


def get_scales():

    return sorted(SCALES.keys())


def get_ids():

    client = kplr.API()

    kois = client.kois(where="koi_period>50", sort="koi_period")

    objs = [{'id': k.kepid, 'name': k.koi_name} for k in kois]

    return objs
