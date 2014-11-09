import os.path

from fabric.api import sudo, cd, put, task, local, env, run, settings, get
from fabric.contrib.files import exists
from fabric.colors import red, yellow
from fabric.utils import abort

APP_NAME = 'keplerphone'
URL = '{}.jonath.in'.format(APP_NAME)
GITHUB_ORGANIZATION = 'bmcfee'
INSTALL_HOME = '/opt'
APP_DIR = os.path.join(INSTALL_HOME, APP_NAME)
REPO = 'git@github.com:{}/{}.git'.format(GITHUB_ORGANIZATION, APP_NAME)
THIS_DIR = os.path.dirname(os.path.realpath(__file__))

env.user = 'ubuntu'
env.hosts = [URL]
env.use_ssh_config = True


def notice(s):
    print(red('### ') + yellow(s, bold=True))


@task
def update_repo():
    notice('Updating application repo from GitHub')

    sudo('mkdir -p {}'.format(INSTALL_HOME))
    sudo('chown {} {}'.format(env.user, INSTALL_HOME))

    ssh_dir = '/home/{}/.ssh'.format(env.user)
    if not exists(ssh_dir):
        run('mkdir -p {}'.format(ssh_dir))
    ssh_id = os.path.join(ssh_dir, 'id_rsa')
    put(os.path.join(THIS_DIR, 'conf', 'github_deploy_key'), ssh_id, use_sudo=True, mode=0600)

    if not exists(os.path.join(APP_DIR, '.git')):
        print(red('FIRST CHECKOUT'))
        with cd(INSTALL_HOME):
            run('git clone {}'.format(REPO))

    with cd(APP_DIR):
        run('git fetch --all')
        run('git checkout -f master')
        run('git pull')


@task
def install_dependencies():
    notice('Updating system packages')
    packages = [
        'git',
        'python-pip',
        'python-setuptools',
        'supervisor',
        'nginx-full',
        'build-essential',
        'python-dev',
        'uwsgi-plugin-python',
        'htop',
        'ipython',
        'swig'
    ]
    sudo('apt-get -y update')
    sudo('apt-get -y upgrade')
    sudo('apt-get -y install {}'.format(' '.join(packages)))


@task
def install_requirements():
    '''Install Python requirements with pip'''
    notice('Installing Python requirements with pip')
    with cd(APP_DIR):
        requirements = os.path.join(APP_DIR, 'requirements.txt')
        sudo('pip install -r {}'.format(requirements))


@task
def configure_supervisor():
    '''Copy Supervisor config from repo'''
    notice('Copying Supervisor config from repo')
    with cd('/etc/supervisor/conf.d'):
        put('conf/supervisor.conf', '{}.conf'.format(APP_NAME), use_sudo=True)


@task
def configure_nginx():
    '''Copy Nginx config from repo'''
    notice('Copying Nginx config from repo')
    if exists('/etc/nginx/sites-enabled/default'):
        sudo('rm /etc/nginx/sites-enabled/default')
    with cd('/etc/nginx/sites-enabled'):
        put('conf/nginx.conf', '{}.conf'.format(APP_NAME), use_sudo=True)


@task
def restart_supervisor():
    notice('Restarting Supervisor')
    sudo('supervisorctl reread')
    sudo('supervisorctl reload')
    sudo('supervisorctl restart {}'.format(APP_NAME))


@task
def restart_nginx():
    notice('Restarting Nginx')
    sudo('/etc/init.d/nginx restart')


@task
def big():
    '''Install all dependencies, clone the repo, and restart.'''
    notice('Installing all dependencies, cloning or updating the repo, and starting or restarting the app.')
    install_dependencies()
    update_repo()
    install_requirements()
    configure_supervisor()
    configure_nginx()
    restart_supervisor()
    restart_nginx()


@task
def small():
    '''Update the repo and restart.'''
    notice('Updating the repo and restarting the app.')
    update_repo()
    install_requirements()
    restart_supervisor()
    restart_nginx()


@task
def rm_pyc():
    '''Recursively delete all pyc files.'''
    local("find . -name '*.pyc' -delete")
    local("find . -name '__pycache__' -delete")
