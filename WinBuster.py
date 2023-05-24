import os
import threading
import time
import requests
import tkinter
import ttkbootstrap as ttk
from urllib.parse import urlparse
from tkinter import Tk, Text, END, messagebox, Scrollbar, filedialog, ttk, StringVar, INSERT
from queue import Queue
from concurrent.futures import ThreadPoolExecutor


class DirBusterGUI:
    def __init__(self, main_root):
        self.root = main_root
        self.root.title("WinBuster Experimental")
        self.root.geometry("780x820")
        self.root.resizable(0, 0)
        self.queue = Queue()  # Initialize a thread-safe Queue
        self.current_url_text = StringVar()
        self.wordlist_progress_text = StringVar(value="0/0")
        self.threads_entry = StringVar()
        self.wordlist_file = None
        self.wordlist_loaded = False
        self.directories_in_queue = StringVar()
        self.directories_in_queue.set("0")
        self.processed_count = 0
        self.processed_count_lock = threading.Lock()
        self.processed_directories = set()
        self.enqueued_urls = set()
        self.progress_value = tkinter.DoubleVar()
        self.scan_complete = False
        self.wordlist_progress = 0
        self.result_lock = threading.Lock()

        # Set up style
        style = ttk.Style()
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5)
        style.configure("TEntry", padding=5)

        # In queue label
        in_queue_label = tkinter.Label(self.root, text="In queue: ")
        in_queue_label.grid(row=3, column=0, padx=27, pady=0, sticky='w')

        # URL label
        self.url_label = ttk.Label(self.root, text="Enter URL:")
        self.url_label.grid(row=0, column=0, padx=23, pady=10, sticky="w")

        # URL input
        self.url_entry = ttk.Entry(self.root, width=108)
        self.url_entry.grid(row=0, column=0, pady=5, padx=100, sticky="w")

        # Wordlist input
        self.wordlist_name_label = ttk.Label(self.root, text="", width=40)
        self.wordlist_name_label.grid(row=1, column=1, padx=10, sticky="w")

        # Browse button
        self.browse_button = ttk.Button(self.root, text="Pick list", width=10, command=self.browse_wordlist)
        self.browse_button.grid(row=1, column=0, padx=18, ipady=10, sticky="w")

        # Number of threads input
        self.threads_label = ttk.Label(self.root, text="Number of threads:")
        self.threads_label.grid(row=1, column=0, padx=100, pady=10, sticky="w")

        self.threads_entry = ttk.Entry(self.root, width=5)
        self.threads_entry.grid(row=1, column=0, pady=5, padx=215, sticky="w")
        self.threads_entry.insert(0, "10")

        # Timeout input
        self.timeout_label = ttk.Label(self.root, text="Timeout (seconds):")
        self.timeout_label.grid(row=1, column=0, padx=270, pady=0, sticky="w")

        self.timeout_entry = ttk.Entry(self.root, width=5)
        self.timeout_entry.grid(row=1, column=0, pady=0, padx=384, sticky="w")
        self.timeout_entry.insert(0, "10")

        # Delay input
        self.delay_label = ttk.Label(self.root, text="Delay (seconds):")
        self.delay_label.grid(row=1, column=0, padx=440, pady=0, sticky="w")

        self.delay_entry = ttk.Entry(self.root, width=5)
        self.delay_entry.grid(row=1, column=0, padx=538, sticky="w")
        self.delay_entry.insert(0, "1")

        # Start
        self.start_button = tkinter.Button(self.root, text="Start", fg='white',
                                           background="#277819", width=10, height=2,
                                           command=self.start)
        self.start_button.grid(row=3, column=0, pady=20, padx=15, sticky="w")

        # Stop button
        self.stop_button = tkinter.Button(self.root, text="Stop", fg='black', height=2,
                                          command=self.stop, width=10)
        self.stop_button.grid(row=3, column=0, pady=20, padx=110, sticky="w")

        # Reset button
        self.reset_button = tkinter.Button(self.root, text="Reset",
                                           bd=4, width=10, height=2,
                                           command=self.reset)
        self.reset_button.grid(row=3, column=0, pady=5, padx=680, sticky="w")

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=660, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=2, padx=10, pady=0, sticky="nw")

        # Add a label to display "Stopping..." message
        self.stopping_label = ttk.Label(self.root, text="", width=40)
        self.stopping_label.grid(row=4, column=2, padx=10, pady=5, sticky="w")

        # Add a label to display label
        self.current_url_label = ttk.Label(self.root, text="Trying URL: ")
        self.current_url_label.grid(column=0, row=4, padx=200, pady=5, sticky="w")
        # Display the current URL being tried
        self.current_url = ttk.Label(self.root, textvariable=self.current_url_text, width=150)
        self.current_url.grid(column=0, row=4, sticky="w", padx=265, pady=5)

        # Progress of list 0/0
        self.wordlist_progress_label = ttk.Label(self.root, textvariable=self.wordlist_progress_text,
                                                 width=10, borderwidth=1, relief="solid")
        self.wordlist_progress_label.grid(row=5, column=0, pady=0, padx=680, sticky="w")

        # Results display for directories in queue
        self.directories_label = ttk.Label(self.root, text="Items in queue: ")
        self.directories_label.grid(row=4, column=0, padx=10, pady=5, sticky="sw")
        self.directories_label = ttk.Label(self.root, textvariable=self.directories_in_queue)
        self.directories_label.grid(row=4, column=0, padx=120, pady=5, sticky="w")

        # Directories label above results box
        self.directory_box_title = ttk.Label(self.root, text="Directories:")
        self.directory_box_title.grid(row=6, column=0, padx=12, pady=0, sticky="sw")

        # Unknown
        self.directories_text = Text(self.root, wrap="word", height=15, width=124,
                                     bg="#1e1e1e", fg="#ffffff",
                                     state="disabled")
        self.directories_text.grid(row=8, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        self.directories_scrollbar = Scrollbar(self.root, command=self.directories_text.yview, bg="#1e1e1e")
        self.directories_scrollbar.grid(row=8, column=3, sticky="nsw")
        self.directories_text.config(yscrollcommand=self.directories_scrollbar.set)

        # Results display for files
        self.files_label = ttk.Label(self.root, text="Files:",
                                     background="#1e1e1e", foreground="#ffffff")
        self.files_label.grid(row=9, column=0, padx=10, pady=0, sticky="w")

        self.files_text = Text(self.root, wrap="word", height=14,
                               width=124, bg="#1e1e1e", fg="#ffffff",
                               state="disabled")
        self.files_text.grid(row=10, column=0, columnspan=3, padx=10, pady=0, sticky="w")

        self.files_scrollbar = Scrollbar(self.root, command=self.files_text.yview, bg="#1e1e1e")
        self.files_scrollbar.grid(row=10, column=3, sticky="nsw")
        self.files_text.config(yscrollcommand=self.files_scrollbar.set)

        # Configure dark mode
        self.root.configure(bg="#1e1e1e")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", padding=5, background="#1e1e1e", foreground="#ffffff")
        style.configure("TButton", padding=5, background="#1e1e1e", foreground="#ffffff")
        style.configure("TEntry", padding=5, fieldbackground="#1e1e1e", foreground="#ffffff")
        style.configure("TProgressbar", troughcolor="#1e1e1e", background="#009688")

        # Update the existing Text and Scrollbar widgets
        self.directories_text.configure(bg="#1e1e1e", fg="#ffffff", state="disabled")
        self.directories_scrollbar.configure(bg="#1e1e1e")

        self.files_text.configure(bg="#1e1e1e", fg="#ffffff", state="disabled")
        self.files_scrollbar.configure(bg="#1e1e1e")

        # Add tag configurations for colored text
        self.directories_text.tag_configure("orange", foreground="orange")

        # Initialize the 'is_running' attribute
        self.is_running = threading.Event()

        style.configure("Stop.TButton", padding=5, background="#360303", foreground="black")

        # Start the main loop
        self.root.mainloop()

    def calculate_score(self, url, sensitive_extensions, sensitive_directories):
        """
        Calculate a score for a URL based on potentially sensitive file extensions and directory names.
        The higher the score, the more likely the URL points to a sensitive resource.
        """
        score = 0
        for ext in sensitive_extensions:
            if url.endswith(ext):
                score += 5
        for directory in sensitive_directories:
            if directory in url.lower():
                score += 3
        return score

    @staticmethod
    def is_valid_url(url):
        """
        Check if a URL is valid. A valid URL must start with "http://" or "https://"
        and must be able to be parsed into its components (scheme, netloc, etc.).
        """
        try:
            result = urlparse(url)
            if all([result.scheme, result.netloc]):
                response = requests.head(url)
                return response.status_code < 400
            return False
        except (ValueError, requests.exceptions.RequestException):
            return False

    def is_valid_input(self, input_value, min_value):
        """
        Check if an input value is a valid integer greater than or equal to a minimum value.
        """
        try:
            value = int(input_value)
            if value >= min_value:
                return True
            else:
                return f"Value must be greater than or equal to {min_value}"
        except ValueError:
            return "Value must be an integer"

    def browse_wordlist(self):
        """
        Open a file dialog to select a wordlist file. Load the wordlist into a queue.
        """
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            if file_path.endswith('.txt'):
                self.queue.queue.clear()
                self.wordlist_file = file_path
                file_name = os.path.basename(file_path)
                self.wordlist_name_label.configure(text=file_name)
                self.wordlist_loaded = True
                print("Wordlist loaded:", file_path)
                with open(file_path, 'r') as wordlist_file:
                    self.wordlist_size = sum(1 for _ in wordlist_file)
                print(self.wordlist_size, "entries.")
                self.wordlist_progress_text.set(f"0/{self.wordlist_size}")
                self.progress.configure(maximum=self.wordlist_size)
            else:
                messagebox.showerror("Error", "Please select a valid wordlist file (.txt)")

    def start(self):
        """
        Start the directory busting process. Validate the input and start the executor.
        """
        if self.is_running.is_set():
            messagebox.showerror("Error", "The program is already running.")
            return
        self.scan_complete = ttk.Label(self.root, text="", width=100)
        self.scan_complete.grid(column=0, row=4, sticky="w", padx=440, pady=5)
        url = self.url_entry.get().strip()
        num_threads = self.threads_entry.get()
        timeout = self.timeout_entry.get()
        delay = self.delay_entry.get()
        if not self.is_valid_input(num_threads, min_value=1) \
                or not self.is_valid_input(timeout, min_value=0) \
                or not self.is_valid_input(delay, min_value=0):
            messagebox.showerror("Error", "Please enter a valid number of threads, timeout, and delay.")
            return
        num_threads = int(num_threads)
        timeout = float(timeout)
        delay = float(delay)
        if url and self.wordlist_loaded and self.is_valid_url(url):
            self.is_running.set()
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            with open(self.wordlist_file, 'r') as wordlist_file:
                wordlist = [line.strip() for line in wordlist_file][self.wordlist_progress:]
            self.wordlist_progress_text.set(f"{self.wordlist_progress}/{self.wordlist_size}")
            self.queue.put(url)
            threading.Thread(target=self.run_executor, args=(num_threads, url, timeout, delay, wordlist)).start()
        else:
            messagebox.showerror("Error", "Please enter a valid URL and wordlist.")

    def run_executor(self, num_threads, url, timeout, delay, wordlist):
        """
        Run the executor in a separate thread. Divide the wordlist among the threads.
        """
        barrier = threading.Barrier(num_threads + 1)
        self.current_url_list = [""] * num_threads
        self.processed_count = 0
        wordlist_chunks = [[] for _ in range(num_threads)]
        for i, word in enumerate(wordlist):
            wordlist_chunks[i % num_threads].append(word)
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            while self.queue.qsize() > 0 or not all([f.done() for f in futures]):
                url = self.queue.get()
                try:
                    futures = [executor.submit(self.dirbuster, url, timeout, delay, barrier, i, wordlist_chunks[i]) for
                               i in
                               range(num_threads)]
                    barrier.wait()
                    for future in futures:
                        if self.is_running.is_set():
                            future.result()
                        else:
                            break
                except Exception as e:
                    print(f"Exception encountered when submitting task to executor: {e}")
        self.stop()

    def stop(self):
        """
        Stop the directory busting process. Update the UI to reflect the stopped state.
        """
        if not self.is_running.is_set():
            messagebox.showerror("Error", "The program is not currently running.")
            return
        self.wordlist_progress = self.processed_count
        if self.queue.qsize() > 0:
            self.animate_stopping_label()
        self.is_running.clear()
        self.start_button.config(state="normal")
        self.reset_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.url_entry.config(state="normal")
        self.threads_entry.config(state="normal")
        self.timeout_entry.config(state="normal")
        self.delay_entry.config(state="normal")
        self.browse_button.config(state="normal")
        self.current_url_text.set("none")
        print("Process stopped")

    def animate_stopping_label(self):
        count = 0
        while not self.is_running.is_set():
            count = (count + 1) % 4
            self.stopping_label.configure(text="Stopping" + "." * count)
            stop_id = self.root.after(500, self.animate_stopping_label)
            self.root.wait_variable(self.is_running)
            self.root.after_cancel(stop_id)
        self.stopping_label.configure(text="")

    def dirbuster(self, base_url, timeout, delay, barrier, thread_id, wordlist):
        session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
        session.headers.update(headers)
        high_score_threshold = 6
        medium_score_threshold = 3

        # Define sensitive extensions and directories here
        sensitive_directories = [
            'admin', 'backup', 'conf', 'config', 'database', 'secret', 'uploads', 'download',
            'log', 'private', 'secure', 'test', 'tmp', 'old', 'data', 'bin', 'etc', 'lib',
            'mail', 'module', 'service', 'system', 'user', 'var', 'wp-admin', 'wp-content',
            'wp-includes'
        ]

        sensitive_extensions = [
            '.sql', '.bak', '.tar', '.gz', '.zip', '.log', '.txt', '.old', '.backup', '.swp',
            '.conf', '.ini', '.htaccess', '.php', '.asp', '.aspx', '.jsp', '.cgi', '.pl',
            '.json', '.xml', '.yml', '.yaml', '.env', '.pwd', '.key', '.cert', '.pem'
        ]

        barrier.wait()  # Wait for all threads to start

        for word in wordlist:
            if not self.is_running.is_set():
                break
            from urllib.parse import urljoin
            url = urljoin(base_url, word)
            self.current_url_list[thread_id] = url
            print(url, "\n")
            self.current_url_text.set(url)
            self.root.update_idletasks()  # Add this line to force an update to the UI
            response = None  # Initialize the response variable to None before the try block
            try:
                response = session.get(url, timeout=timeout)
                self.processed_count += 1
                self.progress.step(amount=+1)
                if self.processed_count >= self.wordlist_size:
                    self.scan_complete = True
                    # scan complete label
                    self.scan_complete = ttk.Label(self.root, text="\o/ Scan Complete \o/", foreground='green')
                    self.scan_complete.grid(column=0, row=4, sticky="w", padx=440, pady=5)

                self.wordlist_progress_text.set(f"{self.processed_count}/{self.wordlist_size}")
                if response.status_code in [200, 204, 301, 302, 307] and response.url.rstrip("/") != base_url.rstrip(
                        "/"):
                    # Provide sensitive_extensions and sensitive_directories as parameters
                    score = self.calculate_score(url, sensitive_extensions, sensitive_directories)
                    content_type = response.headers.get("Content-Type")
                    if content_type and "text/html" in content_type:
                        result_text_widget = self.directories_text
                        if url[-1] == "/" or (response.url != url and response.url[-1] == "/"):
                            if response.url != url:
                                new_path = response.url
                            else:
                                new_path = urljoin(base_url, word)
                            self.queue.put(new_path)
                            self.directories_in_queue.set(str(int(self.directories_in_queue.get()) + 1))
                            added_to_queue_text = " (ADDED TO QUEUE)"

                            # Write the directory to the directories result box
                            with self.result_lock:
                                self.directories_text.configure(state="normal")
                                self.directories_text.insert(END, new_path + "\n")
                                self.directories_text.configure(state="disabled")
                            self.queue.put(new_path)
                            self.directories_in_queue.set(str(int(self.directories_in_queue.get()) + 1))

                            # Update wordlist_size
                            self.wordlist_size += self.wordlist_size
                        else:
                            added_to_queue_text = ""

                    else:
                        result_text_widget = self.files_text
                        added_to_queue_text = ""
                    with self.result_lock:
                        result_text_widget.configure(state="normal")
                        start_index = result_text_widget.index(INSERT)
                        end_index = f"{start_index}+{len(url)}c"
                        result_text_widget.configure(state="disabled")
                    if response.url != url:
                        result = f"{url} --> redirected to --> {response.url}"
                        result_text_widget.insert(END, result + "\n")
                    else:
                        result_text_widget.insert(END, url + added_to_queue_text + "\n")
                    if score >= high_score_threshold:
                        result_text_widget.tag_configure("red", foreground="red")
                        result_text_widget.tag_add("red", start_index, end_index)
                    elif score >= medium_score_threshold:
                        result_text_widget.tag_configure("orange", foreground="orange")
                        result_text_widget.tag_add("orange", start_index, end_index)
                    if added_to_queue_text:
                        start_redirect_index = result_text_widget.index(f"{start_index}+{len(url)}c")
                        if response.url != url:
                            end_redirect_index = result_text_widget.index(
                                f"{start_redirect_index}+{len(' REDIRECT to -> ') + len(response.url) + 7}c")
                        else:
                            end_redirect_index = result_text_widget.index(
                                f"{start_redirect_index}+{len(added_to_queue_text) + 7}c")
                        result_text_widget.tag_configure("green", foreground="green")
                        result_text_widget.tag_add("green", start_redirect_index, end_redirect_index)
                    result_text_widget.see(END)
                    result_text_widget.configure(state="disabled")
            except requests.exceptions.RequestException as e:
                print(f"Exception encountered: ", {e})
                self.processed_count += 1
                pass
            finally:
                time.sleep(delay)
                with self.processed_count_lock:
                    if response and response.url not in self.processed_directories:
                        self.processed_directories.add(response.url)
                        print(f"Processed count: {self.processed_count}")  # Add this line

    def on_closing(self):
        self.is_running.clear()
        self.root.destroy()

    def reset(self):
        self.wordlist_progress = 0
        self.directories_text.configure(state="normal")
        self.directories_text.delete(1.0, END)
        self.directories_text.configure(state="disabled")
        self.files_text.configure(state="normal")
        self.files_text.delete(1.0, END)
        self.files_text.configure(state="disabled")
        self.url_entry.delete(0, END)
        self.progress.configure(value=0)  # Reset the progress bar
        self.current_url_text.set("")
        self.wordlist_progress_text.set("0/0")
        self.wordlist_name_label.configure(text="")
        self.scan_complete = ttk.Label(self.root, text="", width=100)
        self.scan_complete.grid(column=0, row=4, sticky="w", padx=440, pady=5)
        # Reset the threads, timeout, and delay fields to their default values
        self.threads_entry.delete(0, END)
        self.threads_entry.insert(0, "5")
        self.timeout_entry.delete(0, END)
        self.timeout_entry.insert(0, "10")
        self.delay_entry.delete(0, END)
        self.delay_entry.insert(0, "1")


if __name__ == "__main__":
    root = Tk()
    dirbuster_gui = DirBusterGUI(root)
    root.protocol("WM_DELETE_WINDOW", dirbuster_gui.on_closing)
    root.mainloop()
