# IpGui.py
# @Philodox333

                # import
import tkinter as tk
import subprocess
import os
import socket

                # functions
def getOwnIp():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(('8.8.8.8', 80))
        iPAddress = s.getsockname()[0]
    except Exception as ex:
        textBox.insert(tk.END, f'Not able to determine your own IP address: {ex}\n')
        return None
    finally:
        s.close()
    return iPAddress

def getNetworkPrefix(iPAddress):
    return '.'.join(iPAddress.split('.')[:-1])

def scanNetwork():
    ownIP = getOwnIp()
    if not ownIP:
        textBox.insert(tk.END, f'Program is being shut down because your own IP could not be determined.\n')
        return

    networkPrefix = getNetworkPrefix(ownIP)
    activeIPs = []

    textBox.insert(tk.END, f'Scanning IP range {networkPrefix}.1 to {networkPrefix}.254 ...\n')
    textBox.update_idletasks()

    for i in range(1, 255):
        ip = f'{networkPrefix}.{i}'
        response = os.system(f'ping -n 1 -w 100 {ip} > nul')
        if response == 0:
            activeIPs.append(ip)
            if ip == ownIP:
                textBox.insert(tk.END, f'IP {ip} is active (This is your own IP address)\n')
            else:
                textBox.insert(tk.END, f'IP {ip} is active\n')
            textBox.update_idletasks()

    textBox.insert(tk.END, '\nActive IPs with MAC addresses:\n')
    arpTable = getArpTable()
    for ip in activeIPs:
        macAddress = arpTable.get(ip, 'MAC address not found')
        if ip == ownIP:
            textBox.insert(tk.END, f'IP: {ip} (This is your own IP address), MAC: {macAddress}\n')
        else:
            textBox.insert(tk.END, f'IP: {ip}, MAC: {macAddress}\n')

def getArpTable():
    arpTable = {}
    arpOutput = subprocess.check_output('arp -a', shell=True).decode('utf-8')
    lines = arpOutput.splitlines()
    for line in lines:
        if line.strip().startswith('Interface:') or line.strip() == '':
            continue
        parts = line.split()
        if len(parts) >= 2:
            iPAddress = parts[0]
            macAddress = parts[1]
            arpTable[iPAddress] = macAddress
    return arpTable

def getIpConfig():
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp850')
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, result.stdout)
    except Exception as ex:
        textBox.insert(tk.END, f'Error: {ex}')

def getIpConfigAll():
    try:
        process = subprocess.Popen(['ipconfig', '/all'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='cp850')
        output = ""
        for line in process.stdout:
            output += line
            textBox.insert(tk.END, line)
            textBox.update_idletasks()
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, output)
    except Exception as ex:
        textBox.insert(tk.END, f'Error: {ex}')

def runNetstatAn():
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, encoding='cp850')
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, result.stdout)
    except Exception as ex:
        textBox.insert(tk.END, f'Error: {ex}')

def runNetstatO():
    try:
        result = subprocess.run(['netstat', '-o'], capture_output=True, text=True, encoding='cp850')
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, result.stdout)
    except Exception as ex:
        textBox.insert(tk.END, f'Error: {ex}')

                # GUI
root = tk.Tk()
root.title('IP GUI v.1.1')

textBox = tk.Text(root, wrap='word', height=20, width=80)
textBox.pack(padx=10, pady=10)

                # Buttons
buttonIp = tk.Button(root, text='Show IPConfig', command=getIpConfig)
buttonIp.pack(pady=5)

buttonIpAll = tk.Button(root, text='Show IPConfig -all', command=getIpConfigAll)
buttonIpAll.pack(pady=5)

buttonHosts = tk.Button(root, text='Show Hosts', command=scanNetwork)
buttonHosts.pack(pady=5)

buttonNetstatAn = tk.Button(root, text='Run netstat -an', command=runNetstatAn)
buttonNetstatAn.pack(pady=5)

buttonNetstatO = tk.Button(root, text='Run netstat -o', command=runNetstatO)
buttonNetstatO.pack(pady=5)

                # Main Loop
root.mainloop()
