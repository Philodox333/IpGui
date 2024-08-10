# IpGui.py
# @Philodox333

# import
import sys
import subprocess
import socket
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QPushButton, QWidget, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt

#main
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

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateStatus)

    def run(self):
        try:
            self.status_message = "Scanning Network"
            self.dots = 0
            self.timer.start(500)

            ownIP = self.getOwnIp()
            if not ownIP:
                self.output_signal.emit('Program is being shut down because your own IP could not be determined.')
                return

            networkPrefix = self.getNetworkPrefix(ownIP)
            activeIPs = []

            self.status_signal.emit(f'Scanning IP range {networkPrefix}.1 to {networkPrefix}.254 ...')
            for i in range(1, 255):
                ip = f'{networkPrefix}.{i}'
                response = subprocess.run(f'ping -n 1 -w 100 {ip} > nul', shell=True, capture_output=True)
                if response.returncode == 0:
                    activeIPs.append(ip)
                    if ip == ownIP:
                        self.output_signal.emit(f'IP {ip} is active (This is your own IP address)\n')
                    else:
                        self.output_signal.emit(f'IP {ip} is active\n')

            self.output_signal.emit('\nActive IPs with MAC addresses:\n')
            arpTable = self.getArpTable()
            for ip in activeIPs:
                macAddress = arpTable.get(ip, 'MAC address not found')
                if ip == ownIP:
                    self.output_signal.emit(f'IP: {ip} (This is your own IP address), MAC: {macAddress}\n')
                else:
                    self.output_signal.emit(f'IP: {ip}, MAC: {macAddress}\n')

            self.timer.stop()
        except Exception as ex:
            self.timer.stop()
            self.output_signal.emit(f'Error during network scan: {ex}')

    def updateStatus(self):
        dots = '.' * (self.dots % 4)
        self.status_signal.emit(f'{self.status_message}{dots}')
        self.dots += 1

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

        # Window Settings
        self.setWindowTitle('IP GUI v.1.1')
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)

        # Window Flags
        self.setWindowFlags(Qt.WindowType.Window |
                            Qt.WindowType.WindowTitleHint |
                            Qt.WindowType.WindowMinimizeButtonHint |
                            Qt.WindowType.WindowCloseButtonHint)

        # Style of the GUI
        self.setStyleSheet("background-color: #d6e3f3;")

        # Text box
        self.textBox = QTextEdit(self)
        self.textBox.setStyleSheet("color: #2e2e2e; background-color: #f0e5d8;")  # Wärmere Hintergrundfarbe
        self.textBox.setFont(QFont("Consolas", 10))
        self.textBox.setReadOnly(True)
        self.textBox.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # Zeilenumbruch aktivieren

        # Buttons
        buttonStyle = "background-color: rgba(64, 64, 64, 0.8); color: #ffffff;"  # Dunkles Grau, leicht transparent

        buttonIp = QPushButton('Show IPConfig', self)
        buttonIp.clicked.connect(lambda: self.runCommand(['ipconfig'], 'Führe ipconfig aus'))
        buttonIp.setStyleSheet(buttonStyle)

        buttonIpAll = QPushButton('Show IPConfig -all', self)
        buttonIpAll.clicked.connect(lambda: self.runCommand(['ipconfig', '/all'], 'Führe ipconfig /all aus'))
        buttonIpAll.setStyleSheet(buttonStyle)

        buttonHosts = QPushButton('Show Hosts', self)
        buttonHosts.clicked.connect(lambda: self.runNetworkScan('Führe Netzwerkscan aus'))
        buttonHosts.setStyleSheet(buttonStyle)

        buttonNetstatAn = QPushButton('Run netstat -an', self)
        buttonNetstatAn.clicked.connect(lambda: self.runCommand(['netstat', '-an'], 'Führe netstat -an aus'))
        buttonNetstatAn.setStyleSheet(buttonStyle)

        buttonNetstatO = QPushButton('Run netstat -o', self)
        buttonNetstatO.clicked.connect(lambda: self.runCommand(['netstat', '-o'], 'Führe netstat -o aus'))
        buttonNetstatO.setStyleSheet(buttonStyle)

        # Layouts
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(buttonIp)
        buttonLayout.addWidget(buttonIpAll)
        buttonLayout.addWidget(buttonHosts)
        buttonLayout.addWidget(buttonNetstatAn)
        buttonLayout.addWidget(buttonNetstatO)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.textBox, 3)
        mainLayout.addLayout(buttonLayout, 1)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        # status bar
        self.statusBar().showMessage('Ready')

        # timer for stati
        self.statusTimer = QTimer()
        self.statusTimer.timeout.connect(self.updateStatusMessage)
        self.statusMessage = ""
        self.statusDots = 0

    def runCommand(self, command, status_message):
        self.statusMessage = status_message
        self.statusDots = 0
        self.updateStatusMessage()
        self.statusTimer.start(500)  # Update alle 500ms
        self.commandThread = CommandThread(command)
        self.commandThread.output_signal.connect(self.commandFinished)
        self.commandThread.start()

    def runNetworkScan(self, status_message):
        self.statusMessage = status_message
        self.statusDots = 0
        self.updateStatusMessage()
        self.statusTimer.start(500)  # Update alle 500ms

        # Create and start NetworkScanThread
        self.networkScanThread = NetworkScanThread()
        self.networkScanThread.output_signal.connect(self.commandFinished)
        self.networkScanThread.status_signal.connect(self.updateStatusMessageForNetworkScan)
        self.networkScanThread.start()

    def updateStatusMessage(self):
        dots = '.' * (self.statusDots % 4)
        self.textBox.setPlainText(f'{self.statusMessage}{dots}')
        self.statusDots += 1

    def updateStatusMessageForNetworkScan(self, message):
        self.textBox.setPlainText(message)

    def commandFinished(self, output):
        self.statusTimer.stop()
        self.textBox.append(output)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IpGui()
    window.show()
    sys.exit(app.exec())
