# IPGui
# @ETrommer

        #Import
import sys
import subprocess
import socket
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QMenuBar, QMenu, QComboBox, QFileDialog
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import QThread, pyqtSignal


        #Hauptprogramm
class CommandThread(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            result = subprocess.run(self.command, capture_output=True, text=True, encoding='cp850')
            self.output_signal.emit(result.stdout)
        except Exception as ex:
            self.output_signal.emit(f'Error: {ex}')

class NetworkScanThread(QThread):
    output_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def run(self):
        try:
            ownIP = self.getOwnIp()
            if not ownIP:
                self.output_signal.emit('Error: Own IP address could not be retrieved')
                return

            networkPrefix = self.getNetworkPrefix(ownIP)
            activeIPs = []

            self.status_signal.emit(f'Scan IPs from {networkPrefix}.1 to {networkPrefix}.254 ...')

            for i in range(1, 255):
                ip = f'{networkPrefix}.{i}'
                process = subprocess.Popen(f'ping -n 1 -w 100 {ip}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()  # Warten, bis der Ping-Befehl abgeschlossen ist

                if process.returncode == 0:
                    activeIPs.append(ip)
                    if ip == ownIP:
                        self.output_signal.emit(f'IP {ip} ist aktiv (This is your own IP address)\n')
                    else:
                        self.output_signal.emit(f'IP {ip} is aktive\n')

            self.output_signal.emit('\nAktive IPs with MAC adresses\n')
            arpTable = self.getArpTable()
            for ip in activeIPs:
                macAddress = arpTable.get(ip, 'MAC address not found')
                if ip == ownIP:
                    self.output_signal.emit(f'IP: {ip} (This is your own IP address), MAC: {macAddress}\n')
                else:
                    self.output_signal.emit(f'IP: {ip}, MAC: {macAddress}\n')
        except Exception as ex:
            self.output_signal.emit(f'Error while trying to scan network: {ex}')

    def getOwnIp(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(('8.8.8.8', 80))
            iPAddress = s.getsockname()[0]
            s.close()
            return iPAddress
        except Exception as ex:
            return None

    def getNetworkPrefix(self, iPAddress):
        return '.'.join(iPAddress.split('.')[:-1])

    def getArpTable(self):
        arpTable = {}
        try:
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
        except Exception as ex:
            arpTable['Error'] = f'Error retrieving ARP table: {ex}'
        return arpTable

class IpGui(QMainWindow):
    def __init__(self):
        super().__init__()

        # Fenster-Einstellungen
        self.setWindowTitle('IP GUI v.1.3')
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)

        # Menüleiste erstellen
        self.menuBar = self.menuBar()
        self.createMenus()

        # Stile für die GUI
        self.setStyleSheet('''
            QMainWindow {
                background-color: rgba(10, 10, 10, 230);  # Leicht transparentes dunkles Grau
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 200);
                color: #0ff;
                border: 1px solid #00f;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton {
                background-color: rgba(32, 32, 32, 200);
                color: #0ff;
                border: 1px solid #00f;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(32, 32, 32, 220);
            }
        ''')

        # Textfeld
        self.textBox = QTextEdit(self)
        self.textBox.setFont(QFont('Consolas', 10))
        self.textBox.setReadOnly(True)
        self.textBox.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        # Buttons
        buttonHosts = QPushButton('Show Hosts', self)
        buttonHosts.clicked.connect(lambda: self.runNetworkScan('Führe Netzwerkscan aus'))

        # Dropdown-Menü für netstat
        self.netstatComboBox = QComboBox(self)
        self.netstatComboBox.addItems([
            'Run netstat',
            'Run netstat -a',
            'Run netstat -b',
            'Run netstat -n',
            'Run netstat -o',
            'Run netstat -r',
            'Run netstat -s'
        ])
        self.netstatComboBox.currentIndexChanged.connect(self.runNetstat)

        # Dropdown-Menü für ipconfig
        self.ipconfigComboBox = QComboBox(self)
        self.ipconfigComboBox.addItems([
            'Run ipconfig',
            'Run ipconfig -all',
            'Run ipconfig -release',
            'Run ipconfig -renew',
            'Run ipconfig -displaydns',
            'Run ipconfig -flushdns',
            'Run ipconfig -registerdns'
        ])
        self.ipconfigComboBox.currentIndexChanged.connect(self.runIpConfig)

        # Layouts
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(buttonHosts)
        buttonLayout.addWidget(self.netstatComboBox)
        buttonLayout.addWidget(self.ipconfigComboBox)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.textBox, 3)
        mainLayout.addLayout(buttonLayout, 1)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        # Statusleiste
        self.statusBar().showMessage('Ready')
        self.statusBar().setStyleSheet('background-color: rgba(32, 32, 32, 230); color: #0ff; border-top: 1px solid #00f;')

    def createMenus(self):
        # Menü Datei
        fileMenu = self.menuBar.addMenu('File')

        # Save As .txt Aktion
        saveAction = QAction('Save as .txt', self)
        saveAction.triggered.connect(self.saveToFile)
        fileMenu.addAction(saveAction)

        # Exit Aktion
        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

    def runCommand(self, command, statusMessage):
        self.statusMessage = statusMessage
        self.updateStatusMessage()
        self.commandThread = CommandThread(command)
        self.commandThread.output_signal.connect(self.commandFinished)
        self.commandThread.start()

    def runNetworkScan(self, statusMessage):
        self.statusMessage = statusMessage
        self.updateStatusMessage()
        self.networkScanThread = NetworkScanThread()
        self.networkScanThread.output_signal.connect(self.commandFinished)
        self.networkScanThread.status_signal.connect(self.statusMessageUpdated)
        self.networkScanThread.start()

    def runNetstat(self, index):
        netstatCommands = {
            0: ['netstat'],
            1: ['netstat', '-a'],
            2: ['netstat', '-b'],
            3: ['netstat', '-n'],
            4: ['netstat', '-o'],
            5: ['netstat', '-r'],
            6: ['netstat', '-s'],
        }
        command = netstatCommands.get(index)
        if command:
            self.runCommand(command, 'Running netstat')

    def runIpConfig(self, index):
        ipconfigCommands = {
            0: ['ipconfig'],
            1: ['ipconfig', '/all'],
            2: ['ipconfig', '/release'],
            3: ['ipconfig', '/renew'],
            4: ['ipconfig', '/displaydns'],
            5: ['ipconfig', '/flushdns'],
            6: ['ipconfig', '/registerdns'],
        }
        command = ipconfigCommands.get(index)
        if command:
            self.runCommand(command, 'Running ipconfig')

    def commandFinished(self, output):
        self.textBox.append(output)
        self.statusMessage = 'Ready'
        self.updateStatusMessage()

    def statusMessageUpdated(self, status):
        self.statusBar().showMessage(status)

    def updateStatusMessage(self):
        self.statusBar().showMessage(self.statusMessage)

    def saveToFile(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'Text Files (*.txt)')
        if filename:
            with open(filename, 'w') as f:
                f.write(self.textBox.toPlainText())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = IpGui()
    gui.show()
    sys.exit(app.exec())
