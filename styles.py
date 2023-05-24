import tkinter.ttk as ttk


def create_styles():
    style = ttk.Style()

    style.theme_use("clam")
    style.configure("TLabel", padding=5, background="#1e1e1e", foreground="#ffffff")
    style.configure("TButton", padding=5, background="#1e1e1e", foreground="#ffffff")
    style.configure("TEntry", padding=5, fieldbackground="#1e1e1e", foreground="#ffffff")
    style.configure("TProgressbar", troughcolor="#1e1e1e", background="#009688")

    # Add any other custom styles here, for example:
    # style.configure("CustomInQueueLabel.TLabel", padding=10, background="#1e1e1e", foreground="#ffffff")

    return style
