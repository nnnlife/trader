import virtualbox
import time
import gevent
from datetime import datetime, timedelta


class _Machine:
    def __init__(self, vbox, vm_name):
        self.vbox = vbox
        self.vm_name = vm_name
        self.client_name = ''
        self.session = virtualbox.Session()
        self.client_ready = False
        self.launch_time = datetime.now()
        self.vm = self.vbox.find_machine(self.vm_name)
        progress = self.vm.launch_vm_process(self.session, 'gui', [])
        progress.wait_for_completion()

    def set_client_ready(self):
        self.client_ready = True
        
    def get_vm_name(self):
        return self.vm_name

    def is_client_ready(self):
        return self.client_ready

    def stop(self):
        self.session.console.power_down()

    def is_over_time(self):
        if datetime.now() - self.launch_time > timedelta(seconds=1200):
            return True
        return False 

    def reboot(self):
        self.stop()
        # wait until session status is OFF
        # restart again
        while True:
            gevent.sleep(1)
            print('machine state', self.vm.state)
            print('session state', self.session.state)
            if self.vm.state == 1 and self.session.state == 1:
                self.session = virtualbox.Session()
                self.vm = self.vbox.find_machine(self.vm_name)
                self.vm.launch_vm_process(self.session, 'gui', '')
                break

        self.launch_time = datetime.now()


class VBoxControl:
    def __init__(self):
        self.vbox = virtualbox.VirtualBox()
        self.vbox_list = [vm.name for vm in self.vbox.machines]
        self.vbox_machines = []
        self.names = {'win64': 'nnnlife',
                      'win64-trader': 'hhhlife',
                      'vvvlife': 'vvvlife',
                      'wwwlife': 'wwwlife'}
        print('VBOX List', self.vbox_list)

    def get_client_names_not_connected(self):
        client_names = []
        for v in self.vbox_machines:
            if not v.is_client_ready():
                if v.get_vm_name() in self.names:
                    client_names.append(self.names[v.get_vm_name()])
                else:
                    print('Cannot find vm name', v.get_vm_name())
        return client_names

    def get_vm(self, vm_name):
        for vm in self.vbox_machines:
            if vm.get_vm_name() == vm_name:
                return vm
        return None

    def get_vm_by_client_name(self, client_name):
        inv_names = {v: k for k, v in self.names.items()}
        if not client_name in inv_names:
            print('cannot find client_name', client_name)
            return None
    
        return self.get_vm(inv_names[client_name])

    def is_over_time(self, client_name):
        vm = self.get_vm_by_client_name(client_name)
        if vm is None:
            return True
        return vm.is_over_time()


    def reboot_vm(self, client_name):
        vm = self.get_vm_by_client_name(client_name)
        if vm is not None:
            vm.reboot()

    def set_ready(self, client_name):
        vm = self.get_vm_by_client_name(client_name)
        if vm is not None:
            vm.set_client_ready()

    def start_machine(self):
        for m in self.vbox_list:
            print('START Machine', m)
            self.vbox_machines.append(_Machine(self.vbox, m))
            gevent.sleep(60)

    def stop_machine(self):
        """ Use msg to shutdown vbox
        for m in self.vbox_machines:
            print('STOP Machine', m.vm_name)
            m.stop()
            gevent.sleep(60)
        """  
        self.vbox_machines.clear()

if __name__ == '__main__':
    vc = VBoxControl()

    #vc.start_machine()
    import time
    time.sleep(60 * 2)
    #vc.set_ready('nnnlife')
    #print('not connected list', vc.get_client_names_not_connected())
    #print('is over time', vc.is_over_time('nnnlife'))
    #vc.reboot_vm('nnnlife')
    #vc.stop_machine()
