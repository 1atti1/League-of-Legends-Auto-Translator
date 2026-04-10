#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoL Screen Translator - PT-BR
Traduz itens, habilidades e descricoes usando Google Translate (gratis)

Hotkeys:
  F9  - Captura regiao ao redor do mouse (tooltip)
  F10 - Captura a tela inteira
  F11 - Fechar o programa
"""

import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os
import queue
import textwrap
import glob
import shutil

try:
    import mss
    from PIL import Image, ImageEnhance
    import pytesseract
    from pynput import keyboard
    from pynput import keyboard as pynput_keyboard
    from pynput.mouse import Controller as MouseController
    from deep_translator import GoogleTranslator
except ImportError as e:
    print(f"[ERRO] Dependencia faltando: {e}")
    print("Execute:  pip install -r requirements.txt")
    sys.exit(1)

HOTKEY_TOOLTIP = keyboard.Key.f9
HOTKEY_SCREEN  = keyboard.Key.f10
HOTKEY_QUIT    = keyboard.Key.f11

CONFIG = {
    "capture_radius": 150,
    "overlay_opacity": 0.92,
    "debug_mode": False,
}

translate_queue = queue.Queue()
result_queue    = queue.Queue()


# =============================================================================
#  TESSERACT
# =============================================================================

def encontrar_tesseract():
    found = shutil.which("tesseract")
    if found:
        return found
    caminhos = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
        r"D:\Program Files\Tesseract-OCR\tesseract.exe",
        r"D:\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for c in caminhos:
        if os.path.isfile(c):
            return c
    for letra in ["C", "D", "E"]:
        r = glob.glob(f"{letra}:\\*\\Tesseract-OCR\\tesseract.exe")
        if r:
            return r[0]
    try:
        import winreg
        chave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tesseract-OCR")
        pasta, _ = winreg.QueryValueEx(chave, "InstallDir")
        exe = os.path.join(pasta, "tesseract.exe")
        if os.path.isfile(exe):
            return exe
    except Exception:
        pass
    return ""


def configurar_tesseract():
    salvo = os.environ.get("TESSERACT_CMD", "")
    if salvo and os.path.isfile(salvo):
        pytesseract.pytesseract.tesseract_cmd = salvo
        return True
    caminho = encontrar_tesseract()
    if caminho:
        pytesseract.pytesseract.tesseract_cmd = caminho
        pasta = os.path.dirname(caminho)
        os.environ["PATH"] = pasta + os.pathsep + os.environ.get("PATH", "")
        print(f"[OK] Tesseract: {caminho}")
        return True
    return False


# =============================================================================
#  CAPTURA
# =============================================================================

def capturar_tela_inteira():
    with mss.mss() as sct:
        raw = sct.grab(sct.monitors[1])
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def capturar_regiao_mouse(raio=350):
    mouse = MouseController()
    x, y  = mouse.position
    x1 = max(0, x - raio)
    y1 = max(0, y - raio)
    with mss.mss() as sct:
        raw = sct.grab({"top": y1, "left": x1, "width": raio*2, "height": raio*2})
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


# =============================================================================
#  OCR
# =============================================================================

def linha_valida(linha):
    """Filtra linhas com lixo de OCR, chat e codigo."""
    linha = linha.strip()
    if len(linha) < 4:
        return False

    letras = sum(c.isalpha() for c in linha)
    total  = len(linha)

    # Menos de 45% de letras = lixo do HUD/simbolos
    if letras / total < 0.45:
        return False

    # Parece codigo Python/programacao
    indicadores_codigo = ["def ", ".get(", ".set(", "queue", "task =",
                          "translate_", "import ", "return ", "print(",
                          "if task", "sk=", "fila."]
    for ind in indicadores_codigo:
        if ind in linha:
            return False

    # Muitos caracteres de codigo/lixo
    qtd_lixo = sum(1 for c in linha if c in "|~@#^*_=[]{}><(),.;:")
    if qtd_lixo > 4:
        return False

    # Linha muito curta com numeros (HUD de stats)
    if len(linha) < 8 and sum(c.isdigit() for c in linha) > 3:
        return False

    return True


def extrair_texto(img):
    w, h = img.size
    img  = img.resize((w*2, h*2), Image.LANCZOS)
    img  = ImageEnhance.Contrast(img).enhance(2.0)
    img  = ImageEnhance.Sharpness(img).enhance(2.0)
    img  = img.convert("L")
    img  = img.point(lambda p: 255 if p > 110 else 0)
    # PSM 4 = coluna de texto variavel (melhor para tooltips)
    texto = pytesseract.image_to_string(img, lang="eng+ita+por", config="--psm 4 --oem 3")
    linhas = [l.strip() for l in texto.splitlines() if linha_valida(l)]
    # Remove duplicatas mantendo ordem
    vistas = set()
    unicas = []
    for l in linhas:
        if l not in vistas:
            vistas.add(l)
            unicas.append(l)
    return "\n".join(unicas)


# =============================================================================
#  TRADUCAO
# =============================================================================

def traduzir(texto):
    if not texto.strip():
        return "[nenhum texto detectado]"
    try:
        # Divide em blocos de ate 4500 chars (limite do Google)
        blocos = [texto[i:i+4500] for i in range(0, len(texto), 4500)]
        partes = []
        for bloco in blocos:
            r = GoogleTranslator(source="auto", target="pt").translate(bloco)
            partes.append(r or bloco)
        return "\n".join(partes)
    except Exception as e:
        return f"[Erro na traducao: {e}]"


# =============================================================================
#  WORKER
# =============================================================================

def worker_traducao():
    while True:
        task = translate_queue.get()
        if task is None:
            break
        modo = task.get("modo", "tooltip")
        result_queue.put({"status": "processando"})
        try:
            img = capturar_regiao_mouse(CONFIG["capture_radius"]) \
                  if modo == "tooltip" else capturar_tela_inteira()
            texto_raw = extrair_texto(img)
            if not texto_raw.strip():
                result_queue.put({
                    "status": "ok", "original": "",
                    "traducao": "[Nenhum texto encontrado.\nDica: use Borderless Windowed no LoL]"
                })
            else:
                result_queue.put({
                    "status": "ok",
                    "original": texto_raw,
                    "traducao": traduzir(texto_raw),
                })
        except Exception as e:
            result_queue.put({"status": "erro", "mensagem": str(e)})
        translate_queue.task_done()


# =============================================================================
#  OVERLAY
# =============================================================================

class OverlayTraducao(tk.Toplevel):

    def __init__(self, master, x, y, original, traducao):
        super().__init__(master)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-alpha", CONFIG["overlay_opacity"])
        self.configure(bg="#0a0e1a")

        borda = tk.Frame(self, bg="#c89b3c", padx=2, pady=2)
        borda.pack(fill="both", expand=True)

        interior = tk.Frame(borda, bg="#0a0e1a", padx=12, pady=10)
        interior.pack(fill="both", expand=True)

        # Header
        h = tk.Frame(interior, bg="#0a0e1a")
        h.pack(fill="x", pady=(0,6))
        tk.Label(h, text="LoL Translator", bg="#0a0e1a", fg="#c89b3c",
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Button(h, text="X", bg="#0a0e1a", fg="#888", relief="flat",
                  font=("Segoe UI", 10), cursor="hand2", command=self.destroy,
                  activebackground="#1a1e2e", activeforeground="#fff").pack(side="right")

        tk.Frame(interior, bg="#c89b3c", height=1).pack(fill="x", pady=(0,8))

        # Original
        if original:
            tk.Label(interior, text="Original:", bg="#0a0e1a", fg="#555",
                     font=("Segoe UI", 8, "bold")).pack(anchor="w")
            tk.Label(interior, text=original, bg="#0a0e1a", fg="#445",
                     font=("Consolas", 8), justify="left", wraplength=430
                     ).pack(anchor="w", pady=(2,6))
            tk.Frame(interior, bg="#1e2438", height=1).pack(fill="x", pady=(0,8))

        # Traducao
        tk.Label(interior, text="Traducao (PT-BR):", bg="#0a0e1a", fg="#c89b3c",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0,4))
        caixa = tk.Frame(interior, bg="#111827", padx=8, pady=8)
        caixa.pack(fill="x")
        tk.Label(caixa, text=traducao, bg="#111827", fg="#e8dcc8",
                 font=("Segoe UI", 10), justify="left", wraplength=430,
                 anchor="w").pack(anchor="w")

        tk.Label(interior, text="Arraste para mover | fecha em 25s",
                 bg="#0a0e1a", fg="#333", font=("Segoe UI", 7)).pack(pady=(8,0))

        # Posicao
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w2, h2 = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry(f"+{min(x+20, sw-w2-10)}+{min(y+20, sh-h2-10)}")

        for w in [self, borda, interior]:
            w.bind("<ButtonPress-1>", self._ini)
            w.bind("<B1-Motion>",     self._mov)

        self.after(25000, lambda: self.destroy() if self.winfo_exists() else None)

    def _ini(self, e): self._dx, self._dy = e.x, e.y
    def _mov(self, e):
        self.geometry(f"+{self.winfo_x()+e.x-self._dx}+{self.winfo_y()+e.y-self._dy}")


# =============================================================================
#  PAINEL
# =============================================================================

class PainelControle(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("LoL Translator")
        self.geometry("400x310")
        self.resizable(False, False)
        self.configure(bg="#0a0e1a")
        self.wm_attributes("-topmost", True)

        self._overlay = None
        self._status  = tk.StringVar(value="Pronto - pressione F9 ou F10")

        self._ui()
        threading.Thread(target=worker_traducao, daemon=True).start()
        self._hotkeys()
        self._poll()

    def _ui(self):
        hdr = tk.Frame(self, bg="#0c1221", pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="LoL Screen Translator", bg="#0c1221", fg="#c89b3c",
                 font=("Segoe UI", 15, "bold")).pack()
        tk.Label(hdr, text="Google Translate - Gratis - PT-BR", bg="#0c1221",
                 fg="#556", font=("Segoe UI", 8)).pack()

        corpo = tk.Frame(self, bg="#0a0e1a", padx=18, pady=14)
        corpo.pack(fill="both", expand=True)

        info = tk.Frame(corpo, bg="#111827", padx=12, pady=12)
        info.pack(fill="x", pady=(0,14))

        for i, (k, d) in enumerate([
            ("F9",  "Capturar tooltip ao redor do mouse"),
            ("F10", "Capturar tela inteira"),
            ("F11", "Encerrar o programa"),
        ]):
            tk.Label(info, text=k, bg="#111827", fg="#c89b3c",
                     font=("Consolas", 10, "bold"), width=5, anchor="w"
                     ).grid(row=i, column=0, sticky="w")
            tk.Label(info, text=d, bg="#111827", fg="#8899bb",
                     font=("Segoe UI", 9), anchor="w"
                     ).grid(row=i, column=1, sticky="w", padx=8)

        # Slider de raio de captura
        raio_frame = tk.Frame(corpo, bg="#0a0e1a")
        raio_frame.pack(fill="x", pady=(0, 10))

        tk.Label(raio_frame, text="Raio do tooltip (F9):", bg="#0a0e1a",
                 fg="#8899bb", font=("Segoe UI", 8)).pack(side="left")

        self._raio_label = tk.Label(raio_frame, text="150px", bg="#0a0e1a",
                                    fg="#c89b3c", font=("Segoe UI", 8, "bold"), width=5)
        self._raio_label.pack(side="right")

        self._raio_var = tk.IntVar(value=CONFIG["capture_radius"])
        slider = tk.Scale(raio_frame, from_=80, to=400, orient="horizontal",
                          variable=self._raio_var, bg="#0a0e1a", fg="#c89b3c",
                          troughcolor="#111827", highlightthickness=0,
                          showvalue=False, command=self._atualizar_raio)
        slider.pack(side="left", fill="x", expand=True, padx=6)

        bf = tk.Frame(corpo, bg="#0a0e1a")
        bf.pack(fill="x")
        for txt, modo in [("Capturar Tooltip (F9)", "tooltip"), ("Capturar Tela (F10)", "tela")]:
            tk.Button(bf, text=txt, bg="#1a3a5c", fg="#7bc4ff", relief="flat",
                      font=("Segoe UI", 9), cursor="hand2",
                      command=lambda m=modo: self._go(m),
                      activebackground="#1e4a7a"
                      ).pack(side="left", fill="x", expand=True, ipady=8, padx=(0,3))

        sb = tk.Frame(self, bg="#060912", pady=7)
        sb.pack(fill="x", side="bottom")
        tk.Label(sb, textvariable=self._status, bg="#060912", fg="#446",
                 font=("Segoe UI", 8)).pack()

    def _atualizar_raio(self, val):
        CONFIG["capture_radius"] = int(val)
        self._raio_label.config(text=f"{val}px")

    def _go(self, modo):
        self._status.set(f"Capturando {'tooltip' if modo=='tooltip' else 'tela'}...")
        translate_queue.put({"modo": modo})

    def _hotkeys(self):
        def on_press(key):
            try:
                if   key == HOTKEY_TOOLTIP: self._go("tooltip")
                elif key == HOTKEY_SCREEN:  self._go("tela")
                elif key == HOTKEY_QUIT:    self.destroy()
            except Exception:
                pass
        l = pynput_keyboard.Listener(on_press=on_press)
        l.daemon = True
        l.start()

    def _poll(self):
        try:
            while not result_queue.empty():
                r = result_queue.get_nowait()
                if r["status"] == "processando":
                    self._status.set("Processando OCR + traducao...")
                elif r["status"] == "ok":
                    mouse = MouseController()
                    x, y  = mouse.position
                    if self._overlay:
                        try: self._overlay.destroy()
                        except: pass
                    self._overlay = OverlayTraducao(
                        self, x, y, r.get("original",""), r.get("traducao",""))
                    self._status.set("Traducao concluida!")
                    self.after(4000, lambda: self._status.set("Pronto - pressione F9 ou F10"))
                elif r["status"] == "erro":
                    self._status.set(f"Erro: {r.get('mensagem','')}")
        except queue.Empty:
            pass
        self.after(200, self._poll)


# =============================================================================
#  MAIN
# =============================================================================

def carregar_env():
    env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env):
        with open(env) as f:
            for linha in f:
                linha = linha.strip()
                if "=" in linha and not linha.startswith("#"):
                    k, v = linha.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def main():
    carregar_env()

    if not configurar_tesseract():
        root = tk.Tk()
        root.withdraw()
        resp = messagebox.askquestion(
            "Tesseract nao encontrado",
            "O Tesseract OCR nao foi localizado automaticamente.\n\n"
            "Deseja localizar o tesseract.exe manualmente?"
        )
        if resp == "yes":
            from tkinter import filedialog
            exe = filedialog.askopenfilename(
                title="Localize o tesseract.exe",
                filetypes=[("Executavel", "tesseract.exe"), ("Todos", "*.*")],
                initialdir=r"C:\Program Files",
            )
            if exe and os.path.isfile(exe):
                pytesseract.pytesseract.tesseract_cmd = exe
                with open(".env", "a") as f:
                    f.write(f"\nTESSERACT_CMD={exe}\n")
            else:
                sys.exit(1)
        else:
            sys.exit(1)
        root.destroy()

    PainelControle().mainloop()
    translate_queue.put(None)


if __name__ == "__main__":
    main()
