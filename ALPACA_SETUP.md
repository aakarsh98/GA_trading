# 🔑 Alpaca API Setup (Required)

Alpaca changed their API and now requires authentication even for historical data.

## ✅ Quick Setup (5 minutes)

### **Step 1: Create Free Account**
1. Go to: https://alpaca.markets
2. Click "Get Started Free"
3. Sign up (paper trading is 100% free)

### **Step 2: Get API Keys**
1. Log in to Alpaca
2. Go to: https://app.alpaca.markets/paper/dashboard/overview
3. Click "Generate API Keys"
4. Copy your:
   - API Key ID
   - Secret Key

### **Step 3: Set Environment Variables**

**On Mac/Linux:**
```bash
export ALPACA_API_KEY='your_key_here'
export ALPACA_SECRET_KEY='your_secret_here'

# To make permanent, add to ~/.zshrc or ~/.bashrc:
echo "export ALPACA_API_KEY='your_key_here'" >> ~/.zshrc
echo "export ALPACA_SECRET_KEY='your_secret_here'" >> ~/.zshrc
```

**Or create a file:**
Create `.env` file in your script directory:
```
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
```

### **Step 4: Test It**
```bash
cd "/Users/aakarshraj/GG_ Script"
python3 test_alpaca_connection.py
```

---

## 🔄 Alternative: Use yfinance (Daily Data Only)

If you don't want to sign up for Alpaca, I can create a yfinance version that uses daily data instead of intraday.

**Pros:**
- No API keys needed
- Still works great for daily/weekly strategies

**Cons:**
- No intraday data (no 1min, 5min, 15min, 1h)
- Only daily, weekly, monthly

Let me know if you want the yfinance version!

---

## ❓ FAQ

**Q: Is Alpaca really free?**
A: Yes! Paper trading is 100% free forever. No credit card required.

**Q: Will they have my data?**
A: You're only downloading public market data. They don't see your strategies.

**Q: Can I use it for live trading later?**
A: Yes! Same keys work for both paper and live (once you fund account).

**Q: What if I get rate limited?**
A: Free tier has generous limits (200 requests/min). Our scripts stay well under this.
