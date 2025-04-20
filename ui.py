
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import requests
import json
import subprocess
import sys
import os
import threading
import time

class JobStarterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Starter Client")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Store response data for payment processing
        self.job_response_data = None
        self.payment_response_data = None
        self.auto_refresh_active = False
        self.refresh_thread = None
        
        # Payment API configuration
        self.payment_api_url = "https://payment.masumi.network/api/v1/purchase/"
        self.payment_api_token = "iofsnaiojdoiewqajdriknjonasfoinasd"
        self.job_api_url = "http://127.0.0.1:8000"
        
        # Configure the main frame
        main_frame = tk.Frame(root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        
        # Create tabs
        self.tab_control = ttk.Notebook(main_frame)
        
        self.job_tab = tk.Frame(self.tab_control, bg="#f0f0f0")
        self.payment_tab = tk.Frame(self.tab_control, bg="#f0f0f0")
        self.status_tab = tk.Frame(self.tab_control, bg="#f0f0f0")
        self.junk_tab = tk.Frame(self.tab_control, bg="#f0f0f0")
        self.result_tab = tk.Frame(self.tab_control, bg="#f0f0f0")
        
        self.tab_control.add(self.job_tab, text="Start Job")
        self.tab_control.add(self.payment_tab, text="Payment Settings")
        self.tab_control.add(self.status_tab, text="Check Status")
        self.tab_control.add(self.junk_tab, text="Junk Data")
        self.tab_control.add(self.result_tab, text="Results")
        
        self.tab_control.pack(fill="both", expand=True)
        
        # Title - Job Tab
        title_label = tk.Label(self.job_tab, text="Antidote", font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=(10, 20))
        
        # Input section
        input_frame = tk.LabelFrame(self.job_tab, text="Input Parameters", bg="#f0f0f0", font=("Arial", 10, "bold"))
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # Payment Tab
        payment_title = tk.Label(self.payment_tab, text="Payment Settings", font=("Arial", 16, "bold"), bg="#f0f0f0")
        payment_title.pack(pady=(10, 20))
        
        payment_frame = tk.LabelFrame(self.payment_tab, text="API Configuration", bg="#f0f0f0", font=("Arial", 10, "bold"))
        payment_frame.pack(fill="x", padx=10, pady=10)
        
        # Junk Data Tab: 
        #self.root = tk.Label(self.junk_tab, text=self.get_text_data(), font=("Ubuntu Mono", 14, "bold")).pack(pady=50)

        # Result Tab:
        #self.root = tk.Label(self.result_tab, text=self.get_json_data(), font=("Ubuntu Mono", 14, "bold")).pack(pady=50)

        # Payment URL
        tk.Label(payment_frame, text="Payment API URL:", bg="#f0f0f0").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.payment_url = tk.Entry(payment_frame, width=50)
        self.payment_url.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        self.payment_url.insert(0, self.payment_api_url)
        
        # API Token
        tk.Label(payment_frame, text="API Token:", bg="#f0f0f0").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.token_entry = tk.Entry(payment_frame, width=50, show="*")
        self.token_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        self.token_entry.insert(0, self.payment_api_token)
        
        # Network Selection
        tk.Label(payment_frame, text="Network:", bg="#f0f0f0").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.network_var = tk.StringVar(value="Preprod")
        network_options = ["Preprod", "Mainnet", "Preview"]
        network_dropdown = tk.OptionMenu(payment_frame, self.network_var, *network_options)
        network_dropdown.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Payment Type Selection
        tk.Label(payment_frame, text="Payment Type:", bg="#f0f0f0").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.payment_type_var = tk.StringVar(value="Web3CardanoV1")
        payment_options = ["Web3CardanoV1", "OtherOption1", "OtherOption2"]
        payment_dropdown = tk.OptionMenu(payment_frame, self.payment_type_var, *payment_options)
        payment_dropdown.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # Save Button
        save_button = tk.Button(payment_frame, text="Save Settings", command=self.save_payment_settings,
                            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                            activebackground="#45a049", padx=20)
        save_button.grid(row=4, column=1, sticky="e", padx=10, pady=15)
        
        # Purchaser ID
        tk.Label(input_frame, text="Identifier from Purchaser:", bg="#f0f0f0").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.purchaser_id = tk.Entry(input_frame, width=40)
        self.purchaser_id.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        self.purchaser_id.insert(0, "example_purchaser_123")
        
        # Input text
        tk.Label(input_frame, text="Input Text:", bg="#f0f0f0").grid(row=1, column=0, sticky="nw", padx=10, pady=5)
        self.input_text = scrolledtext.ScrolledText(input_frame, width=50, height=5)
        self.input_text.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        self.input_text.insert(tk.END, "Write a hypothesis about the data")
        
        # Server URL
        tk.Label(input_frame, text="Server URL:", bg="#f0f0f0").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.server_url = tk.Entry(input_frame, width=40)
        self.server_url.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        self.server_url.insert(0, f"{self.job_api_url}/start_job")
        
        # Buttons
        button_frame = tk.Frame(self.job_tab, bg="#f0f0f0")
        button_frame.pack(fill="x", pady=10)
        
        self.start_button = tk.Button(button_frame, text="Start Job", command=self.start_job, 
                                   bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                   activebackground="#45a049", padx=20)
        self.start_button.pack(side="left", padx=10)
        
        self.payment_button = tk.Button(button_frame, text="Submit Payment", command=self.submit_payment, 
                                   bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                   activebackground="#0b7dda", padx=20, state=tk.DISABLED)
        self.payment_button.pack(side="left", padx=10)
        
        # Add confirmation button (initially disabled)
        self.confirm_button = tk.Button(button_frame, text="Confirm Purchase", command=self.confirm_purchase, 
                                   bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
                                   activebackground="#FB8C00", padx=20, state=tk.DISABLED)
        self.confirm_button.pack(side="left", padx=10)
        
        self.clear_button = tk.Button(button_frame, text="Clear Output", command=self.clear_output,
                                   bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                                   activebackground="#d32f2f", padx=20)
        self.clear_button.pack(side="left", padx=10)
        
        # Output section
        output_frame = tk.LabelFrame(self.job_tab, text="API Response", bg="#f0f0f0", font=("Arial", 10, "bold"))
        output_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, width=80, height=15, bg="#002b36", fg="#839496", 
                                                  font=("Consolas", 10))
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status Tab
        status_title = tk.Label(self.status_tab, text="Check Status", font=("Arial", 16, "bold"), bg="#f0f0f0")
        status_title.pack(pady=(10, 20))
        
        # Status Type Selection
        status_type_frame = tk.Frame(self.status_tab, bg="#f0f0f0")
        status_type_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(status_type_frame, text="Status Type:", bg="#f0f0f0").pack(side="left", padx=10)
        
        status_types = [
            ("Job Status (Server)", "job"),
            ("Payment Status (Network)", "payment")
        ]
        
        self.status_type_var = tk.StringVar(value="payment")
        for text, value in status_types:
            rb = tk.Radiobutton(status_type_frame, text=text, value=value, 
                             variable=self.status_type_var, bg="#f0f0f0",
                             command=self.on_status_type_change)
            rb.pack(side="left", padx=10)
        
        status_frame = tk.LabelFrame(self.status_tab, text="Status Query", bg="#f0f0f0", font=("Arial", 10, "bold"))
        status_frame.pack(fill="x", padx=10, pady=10)
        
        # ID field
        id_frame = tk.Frame(status_frame, bg="#f0f0f0")
        id_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(id_frame, text="ID/Reference:", bg="#f0f0f0").pack(side="left", padx=10)
        self.status_id = tk.Entry(id_frame, width=50)
        self.status_id.pack(side="left", padx=10, fill="x", expand=True)
        
        # Payment API parameters frame
        self.payment_params_frame = tk.Frame(status_frame, bg="#f0f0f0")
        self.payment_params_frame.pack(fill="x", padx=10, pady=5)
        
        # Endpoint selection
        tk.Label(self.payment_params_frame, text="Endpoint:", bg="#f0f0f0").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.endpoint_var = tk.StringVar(value="purchase")
        endpoint_options = ["purchase", "payment", "registry"]
        endpoint_dropdown = tk.OptionMenu(self.payment_params_frame, self.endpoint_var, *endpoint_options)
        endpoint_dropdown.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Network selection for status
        tk.Label(self.payment_params_frame, text="Network:", bg="#f0f0f0").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.status_network_var = tk.StringVar(value="Preprod")
        network_dropdown = tk.OptionMenu(self.payment_params_frame, self.status_network_var, *network_options)
        network_dropdown.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Include history checkbox
        self.include_history_var = tk.BooleanVar(value=False)
        include_history_cb = tk.Checkbutton(self.payment_params_frame, text="Include History", 
                                          variable=self.include_history_var, bg="#f0f0f0")
        include_history_cb.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Job status parameters frame
        self.job_params_frame = tk.Frame(status_frame, bg="#f0f0f0")
        # Initially hidden, will be shown when job status is selected
        
        # Status check buttons
        status_button_frame = tk.Frame(status_frame, bg="#f0f0f0")
        status_button_frame.pack(fill="x", padx=10, pady=15)
        
        self.check_status_button = tk.Button(status_button_frame, text="Check Status", 
                                           command=self.check_status,
                                           bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                           activebackground="#0b7dda", padx=10)
        self.check_status_button.pack(side="left", padx=5)
        
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_refresh_cb = tk.Checkbutton(status_button_frame, text="Auto-refresh every 15 seconds", 
                                           variable=self.auto_refresh_var, bg="#f0f0f0",
                                           command=self.toggle_auto_refresh)
        self.auto_refresh_cb.pack(side="left", padx=20)
        
        # Status Response section
        status_output_frame = tk.LabelFrame(self.status_tab, text="Status Response", bg="#f0f0f0", font=("Arial", 10, "bold"))
        status_output_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.status_output = scrolledtext.ScrolledText(status_output_frame, width=80, height=15, bg="#002b36", fg="#839496", 
                                                     font=("Consolas", 10))
        self.status_output.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#e0e0e0")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Call once to set the correct visibility based on initial selection
        self.on_status_type_change()
        
        # Configure tags for text styling
        self.configure_text_tags(self.output_text)
        self.configure_text_tags(self.status_output)
    


    def on_status_type_change(self):
        """Change the UI based on selected status type"""
        status_type = self.status_type_var.get()
        
        if status_type == "payment":
            # Show payment params, hide job params
            self.payment_params_frame.pack(fill="x", padx=10, pady=5)
            if self.job_params_frame.winfo_manager():
                self.job_params_frame.pack_forget()
        else:
            # Show job params, hide payment params
            if self.payment_params_frame.winfo_manager():
                self.payment_params_frame.pack_forget()
            self.job_params_frame.pack(fill="x", padx=10, pady=5)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh status checking"""
        if self.auto_refresh_var.get():
            # Enable auto-refresh
            if not self.auto_refresh_active:
                self.auto_refresh_active = True
                self.refresh_thread = threading.Thread(target=self.auto_refresh_task, daemon=True)
                self.refresh_thread.start()
                self.status_var.set("Auto-refresh enabled - checking every 15 seconds")
        else:
            # Disable auto-refresh
            self.auto_refresh_active = False
            self.status_var.set("Auto-refresh disabled")
    
    def auto_refresh_task(self):
        """Background task for auto-refreshing status"""
        while self.auto_refresh_active:
            # Wait for specified interval
            time.sleep(15)
            
            # Only continue if still active
            if self.auto_refresh_active:
                # Perform the status check in the main thread
                self.root.after(0, self.check_status)
    
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
        self.status_var.set("Output cleared")
        self.job_response_data = None
        self.payment_response_data = None
        self.payment_button.config(state=tk.DISABLED)
        self.confirm_button.config(state=tk.DISABLED)
        
    def save_payment_settings(self):
        """Save the payment settings"""
        self.payment_api_url = self.payment_url.get().strip()
        self.payment_api_token = self.token_entry.get().strip()
        messagebox.showinfo("Success", "Payment settings saved successfully!")
            
    def submit_payment(self):
        if not self.job_response_data:
            messagebox.showerror("Error", "No job data available. Please start a job first.")
            return
            
        try:
            # Prepare payment data using values from job response
            payment_data = {
                "identifierFromPurchaser": self.job_response_data.get("identifierFromPurchaser"),
                "blockchainIdentifier": self.job_response_data.get("blockchainIdentifier"),
                "network": self.network_var.get(),
                "sellerVkey": self.job_response_data.get("sellerVkey"),
                "paymentType": self.payment_type_var.get(),
                "submitResultTime": self.job_response_data.get("submitResultTime"),
                "unlockTime": self.job_response_data.get("unlockTime"),
                "externalDisputeUnlockTime": self.job_response_data.get("externalDisputeUnlockTime"),  
                "agentIdentifier": self.job_response_data.get("agentIdentifier"),
                "inputHash": self.job_response_data.get("input_hash")
            }
            
            # Create the curl command
            curl_command = [
                "curl", "-X", "POST",
                self.payment_api_url,
                "-H", "accept: application/json",
                "-H", f"token: {self.payment_api_token}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payment_data)
            ]
            
            # Show the curl command that would be executed
            curl_display = f"""curl -X 'POST' \\
  '{self.payment_api_url}' \\
  -H 'accept: application/json' \\
  -H 'token: {self.payment_api_token}' \\
  -H 'Content-Type: application/json' \\
  -d '{json.dumps(payment_data, indent=2)}'
"""
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "Executing payment command:\n", "command")
            self.output_text.insert(tk.END, curl_display + "\n\n", "curl")
            
            # Execute the command
            self.status_var.set("Running curl command...")
            self.root.update_idletasks()
            
            process = subprocess.Popen(
                curl_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 and stdout:
                # Parse JSON response
                try:
                    json_data = json.loads(stdout)
                    self.payment_response_data = json_data  # Store for later use
                    formatted_response = json.dumps(json_data, indent=2)
                    
                    self.output_text.insert(tk.END, "Payment Response:\n", "response_header")
                    self.output_text.insert(tk.END, formatted_response + "\n\n", "response")
                    
                    # Print parsed response in a more readable format
                    self.output_text.insert(tk.END, "Parsed Payment Response Values:\n", "parsed_header")
                    self.display_parsed_json(self.output_text, json_data)
                    
                    # Update status
                    self.status_var.set("Payment submitted successfully")
                    
                    # Update status tab with payment ID if available
                    if "data" in json_data and "id" in json_data["data"]:
                        payment_id = json_data["data"]["id"]
                        self.status_id.delete(0, tk.END)
                        self.status_id.insert(0, payment_id)
                        self.status_type_var.set("payment")
                        self.on_status_type_change()
                        
                        # Enable confirm button
                        self.confirm_button.config(state=tk.NORMAL)
                        self.output_text.insert(tk.END, "\nClick 'Confirm Purchase' to verify purchase status", "highlight")
                    
                except json.JSONDecodeError:
                    self.output_text.insert(tk.END, "Raw Response (not JSON):\n", "response_header")
                    self.output_text.insert(tk.END, stdout, "response")
                    self.status_var.set("Received non-JSON response")
            else:
                # Handle error
                self.output_text.insert(tk.END, "Error executing curl command:\n", "error")
                self.output_text.insert(tk.END, stderr, "error")
                self.status_var.set("Error executing curl command")
        
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {str(e)}", "error")
            self.status_var.set(f"An error occurred: {str(e)}")
        
        # Configure text tags again just to be safe
        self.configure_text_tags(self.output_text)

    def confirm_purchase(self):
        """Verify purchase status through the payment API"""
        if not self.payment_response_data:
            messagebox.showerror("Error", "No payment data available. Please submit payment first.")
            return
            
        try:
            # Get payment ID if available
            payment_id = None
            if "data" in self.payment_response_data and "id" in self.payment_response_data["data"]:
                payment_id = self.payment_response_data["data"]["id"]
            
            if not payment_id:
                self.output_text.insert(tk.END, "\nError: Could not find payment ID in the payment response.", "error")
                return
                
            # Build the verification URL - this gets the list of purchases
            url = f"{self.payment_api_url}?limit=10&network={self.network_var.get()}&includeHistory=false"
            
            # Create the curl command
            curl_command = [
                "curl", "-X", "GET",
                url,
                "-H", "accept: application/json",
                "-H", f"token: {self.payment_api_token}"
            ]
            
            # Show the curl command that would be executed
            curl_display = f"""curl -X 'GET' \\
  '{url}' \\
  -H 'accept: application/json' \\
  -H 'token: {self.payment_api_token}'
"""
            self.output_text.insert(tk.END, "\n\nVerifying purchase status:\n", "command")
            self.output_text.insert(tk.END, curl_display + "\n\n", "curl")
            
            # Execute the command
            self.status_var.set("Verifying purchase status...")
            self.root.update_idletasks()
            
            process = subprocess.Popen(
                curl_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 and stdout:
                # Parse JSON response
                try:
                    json_data = json.loads(stdout)
                    
                    # Find the purchase in the list
                    purchase_found = False
                    purchase_data = None
                    purchase_status = "Unknown"
                    next_action = "Unknown"
                    
                    if "status" in json_data and json_data["status"] == "success":
                        if "data" in json_data and "Purchases" in json_data["data"]:
                            purchases = json_data["data"]["Purchases"]
                            for purchase in purchases:
                                if purchase.get("id") == payment_id:
                                    purchase_found = True
                                    purchase_data = purchase
                                    purchase_status = purchase.get("onChainState", "Unknown")
                                    if "NextAction" in purchase and purchase["NextAction"]:
                                        next_action = purchase["NextAction"].get("requestedAction", "Unknown")
                                    break
                    
                    # Display verification results
                    self.output_text.insert(tk.END, "Purchase Verification Results:\n", "summary_header")
                    
                    if purchase_found:
                        self.output_text.insert(tk.END, f"• Purchase Found: ", "key")
                        self.output_text.insert(tk.END, "Yes\n", "highlight")
                        
                        self.output_text.insert(tk.END, f"• Purchase ID: ", "key")
                        self.output_text.insert(tk.END, f"{payment_id}\n", "value")
                        
                        self.output_text.insert(tk.END, f"• Status: ", "key")
                        self.output_text.insert(tk.END, f"{purchase_status}\n", "highlight")
                        
                        self.output_text.insert(tk.END, f"• Next Action: ", "key")
                        self.output_text.insert(tk.END, f"{next_action}\n", "action")
                        
                        # Display more detailed information about the purchase
                        self.output_text.insert(tk.END, "\nPurchase Details:\n", "section_header")
                        if purchase_data:
                            self.display_parsed_json(self.output_text, purchase_data)
                            
                            # Save the purchase ID to the Status tab for easier checking
                            self.tab_control.select(self.status_tab)
                            self.status_id.delete(0, tk.END)
                            self.status_id.insert(0, payment_id)
                            self.status_type_var.set("payment")
                            self.on_status_type_change()
                    else:
                        self.output_text.insert(tk.END, f"• Purchase Not Found: ", "key")
                        self.output_text.insert(tk.END, "No purchase found with ID " + payment_id + "\n", "error")
                        
                        # Show all purchases available in the response for debugging
                        self.output_text.insert(tk.END, "\nAvailable Purchases in System:\n", "section_header")
                        if "data" in json_data and "Purchases" in json_data["data"]:
                            purchases = json_data["data"]["Purchases"]
                            for i, purchase in enumerate(purchases):
                                self.output_text.insert(tk.END, f"{i+1}. ID: {purchase.get('id')}, State: {purchase.get('onChainState', 'Unknown')}\n", "value")
                    
                except json.JSONDecodeError:
                    self.output_text.insert(tk.END, "Raw Response (not JSON):\n", "response_header")
                    self.output_text.insert(tk.END, stdout, "response")
                    self.status_var.set("Received non-JSON response")
            else:
                # Handle error
                self.output_text.insert(tk.END, "Error executing curl command:\n", "error")
                self.output_text.insert(tk.END, stderr, "error")
                self.status_var.set("Error executing curl command")
                
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {str(e)}", "error")
            self.status_var.set(f"An error occurred: {str(e)}")
        
        # Configure text tags again just to be safe
        self.configure_text_tags(self.output_text)
    
    def check_status(self):
        """Check the status of a payment or job"""
        status_type = self.status_type_var.get()
        status_id = self.status_id.get().strip()
        
        if not status_id:
            messagebox.showerror("Error", "Please enter an ID to check status.")
            return
            
        try:
            if status_type == "payment":
                # Build the status URL for payment
                network = self.status_network_var.get()
                endpoint = self.endpoint_var.get()
                include_history = "true" if self.include_history_var.get() else "false"
                
                # Check if we're retrieving a specific ID or a list
                if status_id and endpoint == "purchase":
                    url = f"{self.payment_api_url}{status_id}?network={network}&includeHistory={include_history}"
                else:
                    url = f"{self.payment_api_url}?limit=10&network={network}&includeHistory={include_history}"
                
                # Create the curl command
                curl_command = [
                    "curl", "-X", "GET",
                    url,
                    "-H", "accept: application/json",
                    "-H", f"token: {self.payment_api_token}"
                ]
                
                # Show the curl command that would be executed
                curl_display = f"""curl -X 'GET' \\
  '{url}' \\
  -H 'accept: application/json' \\
  -H 'token: {self.payment_api_token}'
"""
                self.status_output.delete(1.0, tk.END)
                self.status_output.insert(tk.END, "Executing status check command:\n", "command")
                self.status_output.insert(tk.END, curl_display + "\n\n", "curl")
                
                # Execute the command
                self.status_var.set("Checking payment status...")
                self.root.update_idletasks()
                
                process = subprocess.Popen(
                    curl_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                
                if process.returncode == 0 and stdout:
                    # Parse JSON response
                    try:
                        json_data = json.loads(stdout)
                        formatted_response = json.dumps(json_data, indent=2)
                        
                        self.status_output.insert(tk.END, "Status Response:\n", "response_header")
                        self.status_output.insert(tk.END, formatted_response + "\n\n", "response")
                        
                        # Find the specific purchase if we're looking at a list
                        if endpoint == "purchase" and "data" in json_data and "Purchases" in json_data["data"]:
                            purchases = json_data["data"]["Purchases"]
                            purchase_found = False
                            
                            for purchase in purchases:
                                if purchase.get("id") == status_id:
                                    purchase_found = True
                                    purchase_state = purchase.get("onChainState", "Unknown")
                                    next_action = "Unknown"
                                    if "NextAction" in purchase and purchase["NextAction"]:
                                        next_action = purchase["NextAction"].get("requestedAction", "Unknown")
                                    
                                    self.status_output.insert(tk.END, "\nPurchase Status Summary:\n", "summary_header")
                                    self.status_output.insert(tk.END, f"• Purchase ID: {status_id}\n", "key_value")
                                    self.status_output.insert(tk.END, f"• State: {purchase_state}\n", "key_value")
                                    self.status_output.insert(tk.END, f"• Next Action: {next_action}\n", "key_value")
                                    
                                    # If there's a transaction, show its details
                                    if "CurrentTransaction" in purchase and purchase["CurrentTransaction"]:
                                        tx = purchase["CurrentTransaction"]
                                        self.status_output.insert(tk.END, f"• Transaction Hash: {tx.get('txHash', 'N/A')}\n", "key_value")
                                        self.status_output.insert(tk.END, f"• Transaction Status: {tx.get('status', 'N/A')}\n", "key_value")
                                    break
                            
                            if not purchase_found:
                                self.status_output.insert(tk.END, "\nPurchase not found with ID: " + status_id, "error")
                        
                        self.status_var.set("Status check completed")
                    except json.JSONDecodeError:
                        self.status_output.insert(tk.END, "Raw Response (not JSON):\n", "response_header")
                        self.status_output.insert(tk.END, stdout, "response")
                        self.status_var.set("Received non-JSON response")
                else:
                    # Handle error
                    self.status_output.insert(tk.END, "Error executing curl command:\n", "error")
                    self.status_output.insert(tk.END, stderr, "error")
                    self.status_var.set("Error executing curl command")
            else:
                # Job status check implementation
                job_id = status_id
                url = f"{self.job_api_url}/check_status/{job_id}"
                
                # Create the curl command
                curl_command = [
                    "curl", "-X", "GET",
                    url,
                    "-H", "accept: application/json"
                ]
                
                # Show the curl command that would be executed
                curl_display = f"""curl -X 'GET' \\
  '{url}' \\
  -H 'accept: application/json'
"""
                self.status_output.delete(1.0, tk.END)
                self.status_output.insert(tk.END, "Executing job status check command:\n", "command")
                self.status_output.insert(tk.END, curl_display + "\n\n", "curl")
                
                # Execute the command
                self.status_var.set("Checking job status...")
                self.root.update_idletasks()
                
                process = subprocess.Popen(
                    curl_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                
                if process.returncode == 0 and stdout:
                    # Parse JSON response
                    try:
                        json_data = json.loads(stdout)
                        formatted_response = json.dumps(json_data, indent=2)
                        
                        self.status_output.insert(tk.END, "Job Status Response:\n", "response_header")
                        self.status_output.insert(tk.END, formatted_response + "\n\n", "response")
                        
                        # Print parsed response in a more readable format
                        self.status_output.insert(tk.END, "Parsed Job Status Response:\n", "parsed_header")
                        self.display_parsed_json(self.status_output, json_data)
                        
                        self.status_var.set("Job status check completed")
                    except json.JSONDecodeError:
                        self.status_output.insert(tk.END, "Raw Response (not JSON):\n", "response_header")
                        self.status_output.insert(tk.END, stdout, "response")
                        self.status_var.set("Received non-JSON response")
                else:
                    # Handle error
                    self.status_output.insert(tk.END, "Error executing curl command:\n", "error")
                    self.status_output.insert(tk.END, stderr, "error")
                    self.status_var.set("Error executing curl command")
        
        except Exception as e:
            self.status_output.insert(tk.END, f"Error: {str(e)}", "error")
            self.status_var.set(f"An error occurred: {str(e)}")
        
        # Configure text tags
        self.configure_text_tags(self.status_output)
        
    def start_job(self):
        """Start a new job by sending a request to the server using curl"""
        try:
            # Get values from UI
            purchaser_id = self.purchaser_id.get().strip()
            input_text = self.input_text.get(1.0, tk.END).strip()
            url = self.server_url.get().strip()
            
            # Prepare the data
            payload = {
                "identifier_from_purchaser": purchaser_id,
                "input_data": {
                    "text": input_text
                }
            }
            
            # Create the curl command
            curl_command = [
                "curl", "-X", "POST",
                url,
                "-H", "accept: application/json",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload)
            ]
            
            # Show the curl command that would be executed
            curl_display = f"""curl -X 'POST' \\
  '{url}' \\
  -H 'accept: application/json' \\
  -H 'Content-Type: application/json' \\
  -d '{json.dumps(payload, indent=2)}'
"""
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "Executing command:\n", "command")
            self.output_text.insert(tk.END, curl_display + "\n\n", "curl")
            
            # Execute the command
            self.status_var.set("Running curl command...")
            self.root.update_idletasks()
            
            process = subprocess.Popen(
                curl_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 and stdout:
                # Parse JSON response
                try:
                    json_data = json.loads(stdout)
                    self.job_response_data = json_data  # Store for later use
                    formatted_response = json.dumps(json_data, indent=2)
                    
                    self.output_text.insert(tk.END, "Job Response:\n", "response_header")
                    self.output_text.insert(tk.END, formatted_response + "\n\n", "response")
                    
                    # Print parsed response in a more readable format
                    self.output_text.insert(tk.END, "Parsed Job Response Values:\n", "parsed_header")
                    self.display_parsed_json(self.output_text, json_data)
                    
                    # Update status
                    job_id = json_data.get("job_id", "Unknown")
                    self.status_var.set(f"Job started successfully. Job ID: {job_id}")
                    
                    # Enable payment button
                    self.payment_button.config(state=tk.NORMAL)
                    
                except json.JSONDecodeError:
                    self.output_text.insert(tk.END, "Raw Response (not JSON):\n", "response_header")
                    self.output_text.insert(tk.END, stdout, "response")
                    self.status_var.set("Received non-JSON response")
            else:
                # Handle error
                self.output_text.insert(tk.END, "Error executing curl command:\n", "error")
                self.output_text.insert(tk.END, stderr, "error")
                self.status_var.set("Error executing curl command")
        
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {str(e)}", "error")
            self.status_var.set(f"An error occurred: {str(e)}")
        
        # Configure text tags
        self.configure_text_tags(self.output_text)
    
    def display_parsed_json(self, text_widget, json_data, prefix=""):
        """Recursively display JSON data in a more readable format"""
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, (dict, list)):
                    text_widget.insert(tk.END, f"{prefix}• {key}: ", "key")
                    text_widget.insert(tk.END, "\n", "value")
                    new_prefix = prefix + "  "
                    self.display_parsed_json(text_widget, value, new_prefix)
                else:
                    text_widget.insert(tk.END, f"{prefix}• {key}: ", "key")
                    text_widget.insert(tk.END, f"{value}\n", "value")
        elif isinstance(json_data, list):
            for i, item in enumerate(json_data):
                if isinstance(item, (dict, list)):
                    text_widget.insert(tk.END, f"{prefix}• Item {i+1}: ", "key")
                    text_widget.insert(tk.END, "\n", "value")
                    new_prefix = prefix + "  "
                    self.display_parsed_json(text_widget, item, new_prefix)
                else:
                    text_widget.insert(tk.END, f"{prefix}• Item {i+1}: ", "key")
                    text_widget.insert(tk.END, f"{item}\n", "value")
        else:
            text_widget.insert(tk.END, f"{prefix}{json_data}\n", "value")
    
    def configure_text_tags(self, text_widget):
        """Configure text tags for styling the output text"""
        text_widget.tag_configure("command", foreground="#00897B")
        text_widget.tag_configure("curl", foreground="#4CAF50")
        text_widget.tag_configure("request", foreground="#039BE5")
        text_widget.tag_configure("response", foreground="#FFC107")
        text_widget.tag_configure("response_header", foreground="#FF9800", font=("Consolas", 10, "bold"))
        text_widget.tag_configure("parsed_header", foreground="#FF5722", font=("Consolas", 10, "bold"))
        text_widget.tag_configure("summary_header", foreground="#673AB7", font=("Consolas", 10, "bold"))
        text_widget.tag_configure("section_header", foreground="#3F51B5", font=("Consolas", 10, "bold"))
        text_widget.tag_configure("key", foreground="#E91E63")
        text_widget.tag_configure("value", foreground="#9C27B0")
        text_widget.tag_configure("key_value", foreground="#2196F3")
        text_widget.tag_configure("error", foreground="#F44336")
        text_widget.tag_configure("highlight", foreground="#FFEB3B", background="#212121")
        text_widget.tag_configure("action", foreground="#8BC34A", font=("Consolas", 10, "bold"))
        text_widget.tag_configure("sub_key", foreground="#6c71c4")
        text_widget.tag_configure("list_item", foreground="#b58900")

if __name__ == "__main__":
    root = tk.Tk()
    app = JobStarterApp(root)
    root.mainloop()
