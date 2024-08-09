# IpGui.py
# @M.Philodox

        #main
import tkinter as tk
import subprocess

def getIpConfig():
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp850')
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, result.stdout)
    except Exception as ex:
        textBox.insert(tk.END, f'Fehler: {ex}')

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
        textBox.insert(tk.END, f'Fehler: {ex}')

        #gui
root = tk.Tk()
root.title('IP GUI')

textBox = tk.Text(root, wrap='word', height=20, width=80)
textBox.pack(padx=10, pady=10)

        #buttons
buttonIp = tk.Button(root, text='Show IPConfig', command=getIpConfig)
buttonIp.pack(pady=5)

buttonIpAll = tk.Button(root, text='Show IPConfig -all', command=getIpConfigAll)
buttonIpAll.pack(pady=5)

root.mainloop()
