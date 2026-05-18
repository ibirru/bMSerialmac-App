import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image, ImageTk





class PortScannerApp:
    def __init__(self, root):
        self.root = root    
        self.root.title("bMSerial")   
        self.root.geometry("700x600")
        self.serial_port = None
        self.reading = False
        
        # Main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header frame for logo and title
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Logo
        try:
            import os
            import sys
            
            # This line finds the correct folder whether running as a script or a PyInstaller EXE
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            image_path = os.path.join(base_path, "logo_header.png")
            
            logo_image = Image.open(image_path)
            logo_image.thumbnail((150, 150), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = ttk.Label(header_frame, image=self.logo_photo)
            logo_label.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            # If logo fails to load, just continue
            pass
        
        # Heading
        #heading_label = ttk.Label(header_frame, text="Uniphos Terminal", font=("Arial", 16, "bold"))
        heading_label = ttk.Label(header_frame, text=" Terminal", font=("Arial", 16, "bold"))
        heading_label.pack(side=tk.LEFT, padx=00)
        
        # Title
        title_label = ttk.Label(main_frame, text="Available Serial Ports", font=("Arial", 12, "bold"))
        title_label.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Scan button
        scan_btn = ttk.Button(main_frame, text="🔄 Scan Ports", command=self.scan_ports)
        scan_btn.grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Ports listbox with scrollbar
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ports_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, height=8, font=("Courier", 10))
        self.ports_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.ports_listbox.yview)
        
        # Bind double-click to open port
        self.ports_listbox.bind('<Double-Button-1>', self.on_port_selected)
        
        # Connection info
        info_frame = ttk.LabelFrame(main_frame, text="Connection Info", padding="5")
        info_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(info_frame, text="Port:").grid(row=0, column=0, sticky=tk.W)
        self.port_label = ttk.Label(info_frame, text="Not connected", foreground="red", font=("Arial", 10, "bold"))
        self.port_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(info_frame, text="Baud Rate:").grid(row=1, column=0, sticky=tk.W)
        self.baud_var = tk.StringVar(value="9600")
        baud_combo = ttk.Combobox(info_frame, textvariable=self.baud_var, 
                                   values=["9600", "115200", "19200", "38400", "57600"], width=15)
        baud_combo.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Connect button
        self.connect_btn = ttk.Button(main_frame, text="📤 Open Selected Port", command=self.connect_port)
        self.connect_btn.grid(row=5, column=0, pady=5, sticky=(tk.W, tk.E), padx=2)
        
        # Disconnect button
        self.disconnect_btn = ttk.Button(main_frame, text="📥 Close Port", command=self.disconnect_port, state=tk.DISABLED)
        self.disconnect_btn.grid(row=5, column=1, pady=5, sticky=(tk.W, tk.E), padx=2)
        
        # Data display
        data_frame = ttk.LabelFrame(main_frame, text="Received Data", padding="5")
        data_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.data_display = scrolledtext.ScrolledText(data_frame, height=8, width=70, state=tk.DISABLED, font=("Courier", 9))
        self.data_display.pack(fill=tk.BOTH, expand=True)
        
        # Export buttons frame
        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=7, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        export_csv_btn = ttk.Button(export_frame, text="📊 Export to CSV", command=self.export_to_csv)
        export_csv_btn.pack(side=tk.LEFT, padx=5)
        
        export_pdf_btn = ttk.Button(export_frame, text="📄 Export to PDF", command=self.export_to_pdf)
        export_pdf_btn.pack(side=tk.LEFT, padx=5)
        
        clear_data_btn = ttk.Button(export_frame, text="🗑️ Clear Data", command=self.clear_data)
        clear_data_btn.pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(6, weight=1)
        main_frame.rowconfigure(7, weight=0)
        
        # Initial scan
        self.scan_ports()
    
    # List all available ports

    def scan_ports(self):
        """Scan and list available serial ports"""
        self.ports_listbox.delete(0, tk.END)
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.ports_listbox.insert(tk.END, "No ports found")
            messagebox.showinfo("Port Scan", "No serial ports detected.")
            return
        
        for port in ports:
            display_text = f"{port.device} - {port.description}"
            self.ports_listbox.insert(tk.END, display_text)
        
        messagebox.showinfo("Port Scan", f"Found {len(ports)} port(s)")
    
    def on_port_selected(self, event):
        """Handle port selection from list"""
        self.connect_port()
    
    def connect_port(self):
        """Connect to selected port"""
        selection = self.ports_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection", "Please select a port first")
            return
        
        selected_text = self.ports_listbox.get(selection[0])
        port_name = selected_text.split(" - ")[0]
        
        try:
            baud_rate = int(self.baud_var.get())
            self.serial_port = serial.Serial(port_name, baud_rate, timeout=1)
            
            self.port_label.config(text=f"✓ {port_name} @ {baud_rate} bps", foreground="green")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"Connected to {port_name}")
            
            # Start reading thread
            self.reading = True
            read_thread = threading.Thread(target=self.read_data, daemon=True)
            read_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open port: {str(e)}")
    
    def disconnect_port(self):
        """Disconnect from port"""
        if self.serial_port:
            self.reading = False
            time.sleep(0.1)
            self.serial_port.close()
            self.serial_port = None
            
            self.port_label.config(text="Not connected", foreground="red")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            
            messagebox.showinfo("Disconnected", "Port closed successfully")
    
    def read_data(self):
        """Read data from serial port continuously"""
        while self.reading and self.serial_port:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('utf-8', errors='ignore')
                    self.display_data(data)
            except Exception as e:
                self.display_data(f"[Error: {str(e)}]\n")
                break

    def display_data(self, data):
        """Display received data in text widget"""
        self.data_display.config(state=tk.NORMAL)
        self.data_display.insert(tk.END, data)
        self.data_display.see(tk.END)
        self.data_display.config(state=tk.DISABLED)
    
    def clear_data(self):
        """Clear all data from display"""
        self.data_display.config(state=tk.NORMAL)
        self.data_display.delete(1.0, tk.END)
        self.data_display.config(state=tk.DISABLED)
        messagebox.showinfo("Cleared", "Data display cleared")
    
    def export_to_csv(self):
        """Export received data to CSV file with headers and title"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"serial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not file_path:
            return
        
        try:
            # Get data from text widget
            data_text = self.data_display.get(1.0, tk.END).strip()
            
            if not data_text:
                messagebox.showwarning("Empty Data", "No data to export")
                return
            
            # Parse lines
            lines = data_text.split('\n')
            lines = [line for line in lines if line.strip()]  # Remove empty lines
            
            if not lines:
                messagebox.showwarning("Empty Data", "No valid data to export")
                return
            
            # Find and extract header metadata and column headers
            header_row = None
            metadata_lines = []
            data_start_idx = 0
            for idx, line in enumerate(lines):
                if line.strip().startswith('Sr.No'):
                    # This is the header line
                    header_line = line
                    # Parse headers from this line
                    delimiter = None
                    if '\t' in header_line:
                        delimiter = '\t'
                    elif ',' in header_line:
                        delimiter = ','
                    
                    if delimiter:
                        header_row = [col.strip() for col in header_line.split(delimiter) if col.strip()]
                    else:
                        header_row = [col for col in re.split(r'\s{2,}|\s*\t\s*', header_line.strip()) if col.strip()]
                    
                    # Data starts after the separator line
                    if idx + 1 < len(lines) and '---' in lines[idx + 1]:
                        data_start_idx = idx + 2
                    else:
                        data_start_idx = idx + 1
                    
                    # Collect all metadata lines before this header
                    metadata_lines = lines[:idx]
                    break
            
            if data_start_idx >= len(lines):
                data_start_idx = 0  # No header found, use all data
            
            # Detect delimiter from data
            delimiter = None
            for line in lines[data_start_idx:]:
                if '\t' in line:
                    delimiter = '\t'
                    break
                elif ',' in line:
                    delimiter = ','
                    break
            
            # Parse data rows
            parsed_data = []
            
            for line in lines[data_start_idx:]:
                # Skip separator lines (lines with mostly dashes)
                if re.match(r'^\s*-+\s*(-\s*)*$', line.strip()):
                    continue
                
                if delimiter:
                    cols = [col.strip() for col in line.split(delimiter) if col.strip()]
                else:
                    # Split on multiple spaces for space-delimited data
                    cols = [col for col in re.split(r'\s{2,}|\s*\t\s*', line.strip()) if col.strip()]
                
                if cols:  # Only add non-empty rows
                    parsed_data.append(cols)
            
            if not parsed_data and not header_row:
                messagebox.showwarning("Empty Data", "No valid data rows found")
                return
            
            # Write to CSV file with metadata, headers and data
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Write metadata lines first (as plain text)
                for meta_line in metadata_lines:
                    if meta_line.strip():
                        csvfile.write(meta_line + '\n')
                
                if metadata_lines and any(line.strip() for line in metadata_lines):
                    csvfile.write("\n")
                
                # Write header row if found
                if header_row:
                    csvfile.write(','.join(header_row) + '\n')
                
                # Write data rows
                for row in parsed_data:
                    csvfile.write(','.join(row) + '\n')
            
            messagebox.showinfo("Success", f"Data exported to CSV successfully!\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export to CSV: {str(e)}")
    
    def export_to_pdf(self):
        """Export received data to PDF file with tabulated data (tab/comma/space delimited)"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"serial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        if not file_path:
            return
        
        try:
            # Get data from text widget
            data_text = self.data_display.get(1.0, tk.END).strip()
            
            if not data_text:
                messagebox.showwarning("Empty Data", "No data to export")
                return
            
            # Parse lines
            lines = data_text.split('\n')
            lines = [line for line in lines if line.strip()]  # Remove empty lines
            
            if not lines:
                messagebox.showwarning("Empty Data", "No valid data to export")
                return
            
            # Find header row and extract it, collect metadata lines
            header_row = None
            metadata_lines = []
            data_start_idx = 0
            for idx, line in enumerate(lines):
                if line.strip().startswith('Sr.No'):
                    # This is the header line
                    header_line = line
                    # Parse headers from this line
                    delimiter = None
                    if '\t' in header_line:
                        delimiter = '\t'
                    elif ',' in header_line:
                        delimiter = ','
                    
                    if delimiter:
                        header_row = [col.strip() for col in header_line.split(delimiter) if col.strip()]
                    else:
                        header_row = [col for col in re.split(r'\s{2,}|\s*\t\s*', header_line.strip()) if col.strip()]
                    
                    # Data starts after the separator line
                    if idx + 1 < len(lines) and '---' in lines[idx + 1]:
                        data_start_idx = idx + 2
                    else:
                        data_start_idx = idx + 1
                    
                    # Collect all metadata lines before this header
                    metadata_lines = lines[:idx]
                    break
            
            if data_start_idx >= len(lines):
                data_start_idx = 0  # No header found, use all data
            
            # Detect delimiter: tab > comma > space
            delimiter = None
            for line in lines[data_start_idx:]:
                if '\t' in line:
                    delimiter = '\t'
                    break
                elif ',' in line:
                    delimiter = ','
                    break
            
            # Parse data into columns and text
            table_data = []
            text_lines = []
            col_count = 0
            
            # Add header row if found
            if header_row:
                table_data.append(header_row)
                col_count = len(header_row)
            
            for line in lines[data_start_idx:]:
                # Skip separator lines (lines with mostly dashes)
                if re.match(r'^\s*-+\s*(-\s*)*$', line.strip()):
                    continue
                
                if delimiter:
                    cols = [col.strip() for col in line.split(delimiter) if col.strip()]
                else:
                    # Split on multiple spaces for space-delimited data
                    cols = [col for col in re.split(r'\s{2,}|\s*\t\s*', line.strip()) if col.strip()]
                
                # Check if this line matches the expected column count (allowing some variance)
                if cols and (col_count == 0 or (len(cols) >= col_count - 1)):
                    table_data.append(cols)
                    col_count = max(col_count, len(cols))
                elif line.strip() and col_count > 0:
                    # This is a text line that doesn't fit the table pattern, preserve it
                    text_lines.append(line.strip())
            
            if not table_data:
                messagebox.showwarning("Empty Data", "No valid data rows found")
                return
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Add metadata lines from export (if any)
            metadata_style = styles['Normal']
            for meta_line in metadata_lines:
                if meta_line.strip():
                    story.append(Paragraph(meta_line.strip(), metadata_style))
            
            if any(line.strip() for line in metadata_lines):
                story.append(Spacer(1, 12))
            
            # Pad all rows to same column count
            for row in table_data:
                while len(row) < col_count:
                    row.append('')
            
            # Calculate column widths for PDF
            col_widths = [500 / col_count] * col_count if col_count > 0 else [500]
            
            # Create table with styling
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E7E6E6')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
            
            # Add any preserved text lines
            if text_lines:
                story.append(Paragraph("<b>Additional Notes:</b>", metadata_style))
                for text_line in text_lines:
                    story.append(Paragraph(text_line, metadata_style))
                story.append(Spacer(1, 12))
            
            # Add data summary
            story.append(Paragraph(f"<b>Total Records:</b> {len(table_data) - 1 if header_row else len(table_data)} | <b>Columns:</b> {col_count}", metadata_style))
            
            # Build PDF
            doc.build(story)
            messagebox.showinfo("Success", f"Data exported to PDF successfully!\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export to PDF: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PortScannerApp(root)
    root.mainloop()


