import argparse
import yaml
import shutil
import sys
import subprocess
from subprocess import check_call, check_output, CalledProcessError
from wok.plugins.kimchi.config import  get_kimchi_version
from wok.config import get_version

REPOS_LIST     = ('production', 'staging')
DISTROS_LIST   = ('centos/8', 'fedora/31', 'ubuntu/19.10', 'debian/10', 'opensuse/15.1', 'all')
JFROG_BASE     = 'https://kimchi.jfrog.io/kimchi/'

HOMEWOK        = '/tmp/wok/'
HOMEKIMCHI     = HOMEWOK + 'src/wok/plugins/kimchi/'

WOK = [
    'git clone https://github.com/kimchi-project/wok.git ' + HOMEWOK
    ] 

KIMCHI = [
    'mkdir -p ' + HOMEKIMCHI,
    'git clone https://github.com/kimchi-project/kimchi.git ' + HOMEKIMCHI ,
    ]

PACKAGES           = {}
PACKAGES['wok']    = WOK
PACKAGES['kimchi'] = KIMCHI
BUILD              = [['./autogen.sh', '--system'], ['make'], ['make','install']]

COMMANDS_OS = {
    'debian' : { 
        'install' : 'apt install -y',
        'update' : 'apt update -y',
        'make' : ['make', 'deb'],
        'pk' : '.deb',
        'pip' : 'sudo -H pip3 install -r ' + HOMEKIMCHI + 'requirements-UBUNTU.txt',
        },
    'fedora' : {
        'install' : 'dnf install -y',
        'update' : 'dnf update -y',
        'make' : ['make', 'rpm'],
        'pk' : '.rpm',
        'pip' : 'sudo -H pip3 install -r ' + HOMEKIMCHI + 'requirements-FEDORA.txt',
    },
    'opensuse/LEAP' : {
        'install' : 'zypper install -y',
        'update' : 'zypper update -y',
        'make' : ['make', 'rpm'],
        'pk' : '.rpm',
        'pip' : 'sudo -H pip3 install -r ' + HOMEKIMCHI + 'requirements-OPENSUSE-LEAP.txt',
    },
}

def usage():

    '''
    # Handle parameters

    @param repo string repository
    @param distro string distro
    @param user string JFROG user
    @param password string Token JFROG
    '''

    parser = argparse.ArgumentParser(
        description='python install.py -r production -d rhel/7 -u username -p password ',
    )

    parser.add_argument("-r", "--repo", choices=REPOS_LIST, required=True)
    parser.add_argument("-d", "--distro", choices=DISTROS_LIST, default="all")
    parser.add_argument("-u", "--user", help="Account name at %s. This account needs to be granted to write in \
        the repository." % (JFROG_BASE), metavar=("<username>"),required=True)
    parser.add_argument("-p", "--password", help="Token at %s. This token needs to be granted to write in."
            % (JFROG_BASE),metavar=("<password>"),required=True)
 
    args  = parser.parse_args()
    repo  = args.repo

    if args.distro == "all":
        distros = DISTROS_LIST
        distros.remove("all")
    else:
        distros = [args.distro]

    return repo, distros, args.user, args.password

def run_cmd(command):

    '''
    Run the given command using check_call and verify its return code.
    @param str command command to be executed
    '''

    try:
        check_call(command.split())
    except CalledProcessError as e:
        print('An exception h:as occurred: {0}'.format(e))
        sys.exit(1)

def execute_cmd(list, step):

    '''
    Execute the given commands using run_cmd function
    @param list list commands to be executed
    @param step str name of the comand to be executed
    '''
    print('Step: %s' % (step))
    for item in list:
        run_cmd(item)

def run_build(list, dir):
    '''
    Execute the given commands in other directory
    @param list list commands to be executed
    @param dir str directory path
    '''
    try:
        build = subprocess.Popen(list, cwd=dir)
        build.wait()
    except CalledProcessError as e:
        print('An exception has occurred: {0}'.format(e))
        sys.exit(1)

def curl_cmd(repo, distro_name, distro, package_name, user, password, path, component):
    '''
    Move package to JFROG repository
    @param str repo repo 
    @param str distro_name distro name
    @param str distro distro name and version
    @param str package_name package name
    @param str user JFROG user
    @param str password JFROG password
    @param str path path to package
    @param str component component name
    '''

    if distro_name == 'debian' or distro_bame == 'ubuntu':
        cmd = 'curl --silent -u%s:%s -XPUT \
            https://kimchi.jfrog.io/kimchi/%s/%s;deb.distribution=%s;deb.component=%s;deb.architecture=noarch -T %s' \
            % (user, password, distro, package_name, distro, component, path)
    elif distro_name == 'staging':
        cmd = 'curl --silent -u%s:%s -XPUT https://kimchi.jfrog.io/kimchi/staging/%s/ -T %s' \
            % (user, password, distro, path)
    else:
        cmd = 'curl --silent -u%s:%s -XPUT https://kimchi.jfrog.io/kimchi/%s/ -T %s' % (user, password, distro, path)

    execute_cmd([cmd], 'Moving package to JFROG')

def install_dependencies(distro, pm):

    '''
    Install package dependencies
    @param str distro distro name
    @param str pm package manager
    '''

    packages = []
    for file in (HOMEWOK + 'dependencies.yaml', HOMEKIMCHI + 'dependencies.yaml' ):
        with open(file, 'r') as dep_file:
            packages_list = yaml.load(dep_file, Loader=yaml.Loader)
            if 'kimchi' in str(dep_file):
                new_distro = 'ubuntu'
            else:
                new_distro = distro
            packages.append(' '.join([str(elem) for elem in packages_list['development-deps']['common']]))
            packages.append(' '.join([str(elem) for elem in packages_list['development-deps'][new_distro]]))
            packages.append(' '.join([str(elem) for elem in packages_list['runtime-deps']['common']]))
            packages.append(' '.join([str(elem) for elem in packages_list['runtime-deps'][new_distro]]))
        
            for package in packages:
                execute_cmd([COMMANDS_OS[pm]['install'] + ' ' + package], 'Installing necessary packages')
    
    execute_cmd(['sudo -H pip3 install -r ' + HOMEWOK+ 'requirements-dev.txt'], 'Installing requirements')
    execute_cmd(['sudo -H pip3 install -r ' + HOMEKIMCHI+ 'requirements-dev.txt'], 'Installing requirements')
    
def main():
   
    repo, distros, user, password  = usage()
    kimchi_version = get_kimchi_version()
    wok_version = get_version()

    for distro in distros:
        distro_name = distro.split("/")
        if distro_name[0] == 'ubuntu':
            pm = 'debian'
        else:
            pm = distro_name[0]
         
        try:
            shutil.rmtree(HOMEWOK)
        except:
            pass
            
        execute_cmd([COMMANDS_OS[pm]['update']], 'Updating system')
        execute_cmd(PACKAGES['wok'], 'Cloning Wok')
        execute_cmd(PACKAGES['kimchi'], 'Cloning Kimchi')
        install_dependencies(distro_name[0], pm)
        execute_cmd([COMMANDS_OS[pm]['pip']],'Installing Pip packages') 
        
        for item in BUILD:
            
            run_build(item, HOMEWOK)
            run_build(item, HOMEKIMCHI)
            
        run_build(COMMANDS_OS[pm]['make'], HOMEWOK)
        run_build(COMMANDS_OS[pm]['make'], HOMEKIMCHI)
                 
        wok_package    = 'wok-' + wok_version + '.' + distro_name[0] + '.noarch' + COMMANDS_OS[pm]['pk']
        kimchi_package = 'kimchi-' + kimchi_version + '.noarch' + COMMANDS_OS[pm]['pk']
        curl_cmd(repo, distro_name[0], distro, wok_package, user, password, HOMEWOK + wok_package, 'wok')
        curl_cmd(repo, distro_name[0], distro, kimchi_package, user, password, HOMEKIMCHI + kimchi_package, 'kimchi')

    print("All Good, check JFROG")
    
if __name__ == "__main__":
    main()
