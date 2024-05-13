# the shit

![demo](https://github.com/openup-gemma/linux-command-corrector/assets/64704608/5088beca-d82e-456f-aa9b-5609616a4439)

## how to use

### 0. clone
```
git clone https://github.com/openup-gemma/linux-command-corrector.git
```

### 1. virtual environment
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. google api key
- rename `.env.example` to `.env`
- enter `GOOGLE_API_KEY` in `.env`
```
GOOGLE_API_KEY=your-api-key
```

### 3. build
```
pyinstaller -w -F --add-data "$(pwd)/.env:." command_corrector.py
```

### 4. setting
```
source setup.sh
```

### 5. run
```
shit
```

## reference
- [smart-ass](https://github.com/geoff-yoon-dev/smart-ass)
- [thefuck](https://github.com/nvbn/thefuck)