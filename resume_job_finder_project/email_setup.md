# 📧 Email Setup Guide for Resume Job Finder

## 🔧 SMTP Configuration

### **For Gmail Users (Recommended)**

#### **Step 1: Enable 2-Factor Authentication**
1. Go to your Google Account settings
2. Navigate to "Security"
3. Enable "2-Step Verification"

#### **Step 2: Generate App Password**
1. Go to Google Account settings
2. Navigate to "Security" → "2-Step Verification"
3. Click "App passwords" (at the bottom)
4. Select "Mail" and "Windows Computer"
5. Click "Generate"
6. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

#### **Step 3: Configure Environment Variables**
Create a `.env` file in your project directory:

```env
# Gmail SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_character_app_password
NOTIFICATION_EMAIL=your_email@gmail.com
```

### **For Outlook/Hotmail Users**

#### **Step 1: Enable App Passwords**
1. Go to Microsoft Account settings
2. Navigate to "Security"
3. Enable "Two-step verification"
4. Generate an app password

#### **Step 2: Configuration**
```env
# Outlook SMTP Configuration
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@outlook.com
```

### **For Yahoo Users**

#### **Step 1: Generate App Password**
1. Go to Yahoo Account Security
2. Enable "2-step verification"
3. Generate an app-specific password

#### **Step 2: Configuration**
```env
# Yahoo SMTP Configuration
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your_email@yahoo.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@yahoo.com
```

## 🚀 Quick Setup Script

I'll create a setup script to help you configure email settings easily:

```python
# email_setup.py
import os
import getpass
from pathlib import Path

def setup_email_config():
    print("📧 Email Configuration Setup")
    print("=" * 40)
    
    # Get email provider
    print("Choose your email provider:")
    print("1. Gmail")
    print("2. Outlook/Hotmail")
    print("3. Yahoo")
    print("4. Custom SMTP")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        smtp_server = "smtp.gmail.com"
        smtp_port = "587"
    elif choice == "2":
        smtp_server = "smtp-mail.outlook.com"
        smtp_port = "587"
    elif choice == "3":
        smtp_server = "smtp.mail.yahoo.com"
        smtp_port = "587"
    elif choice == "4":
        smtp_server = input("Enter SMTP server: ").strip()
        smtp_port = input("Enter SMTP port: ").strip()
    else:
        print("❌ Invalid choice")
        return
    
    # Get email credentials
    email = input("Enter your email address: ").strip()
    password = getpass.getpass("Enter your app password: ")
    
    # Create .env file
    env_content = f"""# Email Configuration
SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
SMTP_USERNAME={email}
SMTP_PASSWORD={password}
NOTIFICATION_EMAIL={email}

# OpenAI API Key (if you have one)
OPENAI_API_KEY=your_openai_api_key_here
"""
    
    # Write to .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n✅ Email configuration saved to .env file!")
    print("🔒 Your credentials are stored securely")
    print("\n📋 Next steps:")
    print("1. Test your email configuration")
    print("2. Run the resume job finder")
    print("3. Choose email notifications when prompted")

if __name__ == "__main__":
    setup_email_config()
```

## 🧪 Testing Email Configuration

### **Test Script**
```python
# test_email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_email_config():
    # Load environment variables
    load_dotenv()
    
    # Get SMTP settings
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    notification_email = os.getenv('NOTIFICATION_EMAIL')
    
    if not all([smtp_server, smtp_username, smtp_password, notification_email]):
        print("❌ Missing email configuration")
        return False
    
    try:
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = notification_email
        msg['Subject'] = "🧪 Resume Job Finder - Email Test"
        
        body = """
        This is a test email from Resume Job Finder.
        
        If you received this email, your SMTP configuration is working correctly!
        
        You can now use email notifications in the Resume Job Finder application.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email test successful!")
        print(f"📧 Test email sent to: {notification_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return False

if __name__ == "__main__":
    test_email_config()
```

## 🔒 Security Best Practices

### **1. Use App Passwords**
- Never use your main account password
- Generate app-specific passwords
- Revoke app passwords when not needed

### **2. Secure Storage**
- Store credentials in `.env` file
- Add `.env` to `.gitignore`
- Never commit credentials to version control

### **3. Regular Updates**
- Change app passwords periodically
- Monitor account activity
- Use strong, unique passwords

## 🐛 Troubleshooting

### **Common Issues:**

#### **1. "Authentication failed"**
- Check if 2-factor authentication is enabled
- Verify app password is correct
- Ensure you're using app password, not account password

#### **2. "Connection refused"**
- Check SMTP server and port
- Verify firewall settings
- Try different ports (587, 465, 25)

#### **3. "Username or password incorrect"**
- Double-check email address
- Verify app password format
- Try regenerating app password

#### **4. "SSL/TLS required"**
- Ensure `server.starttls()` is called
- Check if port 587 is used
- Verify SSL/TLS settings

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your email provider's SMTP settings
3. Test with a simple email client first
4. Contact your email provider's support

---

**Happy emailing! 📧✨** 