import os
import subprocess
import ctypes
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import os.path
import threading
from ttkthemes import ThemedStyle

# Definir variáveis de ambiente para Tcl/Tk
os.environ['TCL_LIBRARY'] = r'C:\Users\GabrielNicolai\AppData\Local\Programs\Python\Python313\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\GabrielNicolai\AppData\Local\Programs\Python\Python313\tcl\tk8.6'

# Extensões de arquivos de lixo
rubbishExt = ['.tmp', '.bak', '.old', '.wbk', '.xlk', '_mp', '.gid', '.chk', '.syd', '.$$$', '.@@@', ".~*"]

def GetDrives():
    drives = [f"{chr(i)}:/" for i in range(65, 91) if os.path.isdir(f"{chr(i)}:/")]
    return tuple(drives)

def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    else:
        # Reexecutar o script com permissões de administrador
        params = ' '.join([f'"{param}"' for param in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit()

def run_command(command):
    subprocess.run(f'start cmd /k {command}', shell=True)

class Window:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Limpador de lixo - Por Gabriel di Nicolai")
        self.root.geometry("720x512")

        # mudar o tema
        self.style = ThemedStyle(self.root)
        self.style.set_theme("adapta")

        # criar o menu
        menu_bar = tk.Menu(self.root, font=('Arial', 13))

        system_menu = tk.Menu(menu_bar, tearoff=0, font=('Arial', 13))
        clean_menu = tk.Menu(menu_bar, tearoff=0, font=('Arial', 13))

        clean_menu.add_command(label="Escanear…", command=self.MenuScanRubbish)
        clean_menu.add_command(label="Limpar…", command=self.MenuDelRubbish)
        menu_bar.add_cascade(label="Opções", menu=clean_menu)

        system_menu.add_command(label="Sobre", command=self.MenuAbout)
        system_menu.add_command(label="DISM", command=self.run_dism)
        system_menu.add_command(label="SFC", command=self.run_sfc)
        system_menu.add_command(label="CHKDSK", command=self.run_chkdsk)
        system_menu.add_command(label="Sair", command=self.MenuExit)
        menu_bar.add_cascade(label="Mais…", menu=system_menu)

        self.root.config(menu=menu_bar)

        # mostra informacoes
        self.progress_var = tk.StringVar()
        self.progress_var.set(' Status…')
        self.progress = ttk.Label(self.root, textvariable=self.progress_var, anchor=tk.W)
        self.progress.place(x=10, y=370, width=700, height=25)

        # mostra a lista de pastas
        self.flist = tk.Text(self.root, wrap="none", font=('Arial', 15))
        self.flist.place(x=10, y=80, width=700, height=280)

        # scroll para a lista de pastas
        self.vscroll = ttk.Scrollbar(self.root, command=self.flist.yview)
        self.vscroll.place(x=700, y=80, height=280)
        self.flist['yscrollcommand'] = self.vscroll.set

        # adicionar botões de escanear e limpar
        self.scan_button = ttk.Button(self.root, text="Escanear", command=self.MenuScanRubbish)
        self.scan_button.place(x=10, y=400, width=120, height=40)

        self.clean_button = ttk.Button(self.root, text="Limpar", command=self.MenuDelRubbish)
        self.clean_button.place(x=150, y=400, width=120, height=40)

        # adicionar botão de interromper
        self.stop_button = ttk.Button(self.root, text="Interromper", command=self.stop_operation, state=tk.DISABLED)
        self.stop_button.place(x=290, y=400, width=120, height=40)

        # adicionar título
        self.title_label = ttk.Label(self.root, text="Limpador de arquivos temporários", font=('Arial', 20, 'bold'))
        self.title_label.place(relx=0.5, y=10, anchor=tk.CENTER)

        # adicionar descrição
        self.desc_label = ttk.Label(self.root, text="Clique em Escanear para encontrar arquivos temporários e em Limpar para removê-los", font=('Arial', 12))
        self.desc_label.place(relx=0.5, y=50, anchor=tk.CENTER)

        self.stop_event = threading.Event()

    def MainLoop(self):
        self.root.mainloop()

    def MenuAbout(self):
        messagebox.showinfo("Removedor de Lixo", "Função: Escanear e deletar lixo do PC")

    def MenuExit(self):
        self.root.quit()

    def MenuScanRubbish(self):
        result = messagebox.askquestion("Removedor de Lixo", "Escanear agora?")
        if result == 'no':
            return
        self.drives = GetDrives()
        self.stop_event.clear()
        self.stop_button.config(state=tk.NORMAL)
        t = threading.Thread(target=self.ScanRubbish, args=(self.drives,))
        t.start()

    def MenuDelRubbish(self):
        result = messagebox.askquestion("Removedor de Lixo", "Deletar todo o lixo?")
        if result == 'no':
            return
        self.drives = GetDrives()
        self.stop_event.clear()
        self.stop_button.config(state=tk.NORMAL)
        t = threading.Thread(target=self.DeleteRubbish, args=(self.drives,))
        t.start()

    def ScanRubbish(self, scanpath):
        global rubbishExt
        total = 0
        filesize = 0
        for drive in scanpath:
            for root, dirs, files in os.walk(drive):
                if self.stop_event.is_set():
                    self.progress_var.set("Operação interrompida pelo usuário.")
                    self.stop_button.config(state=tk.DISABLED)
                    return
                try:
                    for fil in files:
                        filesplit = os.path.splitext(fil)
                        if filesplit[1] in rubbishExt:
                            fname = os.path.join(os.path.abspath(root), fil)
                            if not os.access(fname, os.R_OK):
                                print(f"Sem permissão para ler o arquivo: {fname}")
                                continue
                            filesize += os.path.getsize(fname)
                            if total % 20 == 0:
                                self.flist.delete(1.0, tk.END)
                            self.flist.insert(tk.END, fname + '\n')
                            l = len(fname)
                            if l > 60:
                                self.progress_var.set(fname[:30] + '...' + fname[l-30:l])
                            else:
                                self.progress_var.set(fname)
                            total += 1
                except Exception as e:
                    print(e)
                    pass
        self.progress_var.set(f"Foram encontradas {total} pastas removíveis, que estão ocupando {filesize/1024/1024:.2f} MB de espaço no disco!")
        self.stop_button.config(state=tk.DISABLED)

    def DeleteRubbish(self, scanpath):
        global rubbishExt
        total = 0
        filesize = 0
        for drive in scanpath:
            for root, dirs, files in os.walk(drive):
                if self.stop_event.is_set():
                    self.progress_var.set("Operação interrompida pelo usuário.")
                    self.stop_button.config(state=tk.DISABLED)
                    return
                try:
                    for fil in files:
                        filesplit = os.path.splitext(fil)
                        if filesplit[1] in rubbishExt:
                            fname = os.path.join(os.path.abspath(root), fil)
                            if not os.access(fname, os.W_OK):
                                print(f"Sem permissão para deletar o arquivo: {fname}")
                                continue
                            filesize += os.path.getsize(fname)
                            try:
                                os.remove(fname)
                                l = len(fname)
                                if l > 50:
                                    fname = fname[:25] + "..." + fname[l-25:l]
                                if total % 15 == 0:
                                    self.flist.delete(1.0, tk.END)
                                self.flist.insert(tk.END, 'Deletado ' + fname + '\n')
                                self.progress_var.set(fname)
                                total += 1
                            except:
                                pass
                except Exception as e:
                    print(e)
                    pass
        self.progress_var.set(f"Foram deletados {filesize/1024/1024:.2f} MB de pastas removíveis = Recuperando {filesize/1024/1024:.2f} MB de espaço de disco.")
        self.stop_button.config(state=tk.DISABLED)

    def run_dism(self):
        run_command("dism /online /cleanup-image /restorehealth")

    def run_sfc(self):
        run_command("sfc /scannow")

    def run_chkdsk(self):
        run_command("chkdsk /f /r")

    def stop_operation(self):
        self.stop_event.set()

if __name__ == "__main__":
    if run_as_admin():
        window = Window()
        window.MainLoop()