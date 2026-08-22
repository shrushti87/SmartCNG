# SmartCNG Platform Instructions

This definitive file contains everything you need to start, manage, and log into your custom SmartCNG platform.

## How to Run the Website

Because this project uses strict dependencies managed in an isolated python environment, you **must run the project using the Virtual Environment (`venv`)** or the website will throw an error. 

If you are using Windows PowerShell within your `clone` folder, run these exact commands in order:

### 1. Start the Virtual Environment
```powershell

.\venv\Scripts\Activate.ps1
```
*(You will know it worked if you see `(venv)` appear on the left side of your terminal line)*

### 2. Start the Server
```powershell

python manage.py runserver
```

*(Alternatively, you can just run this single combined line without activating anything)*:
```powershell

.\venv\Scripts\python manage.py runserver
```

---

## Credentials & Roles

Your platform is completely isolated with Dual-Role access.

### Master Administrator Credentials
This user has total access to both the visual **Admin Control Panel** and the **Backend Database Viewer**.

- **Username**: `admin`
- **Password**: `admin123`

You can also create a new master administrator anytime by running: 
```powershell

.\venv\Scripts\python manage.py createsuperuser
```

---

## Navigating the Platform
Once the server is explicitly running, you can click on the following local links to jump instantly to the respective domains:

- **Main System Website (Customer Facing):** 
  [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
  
- **Admin Portal Dashboard:** 
  [http://127.0.0.1:8000/admin-dashboard/](http://127.0.0.1:8000/admin-dashboard/)
  
- **Under-the-hood Database Inspector:** 
  [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

##  Useful Commands

**1. Fetch latest real-world CNG stations from OpenStreetMap (Overpass API):**
*(This defaults to Nashik region, you can edit the command's config to fetch anywhere)*
```powershell

.\venv\Scripts\python manage.py fetch_stations --radius 20000
```

---

## Fresh Installation (Running on a New Computer)

If you copy this project folder to a **completely different machine**, you will need to re-initialize the environment so that all Python dependencies install securely without breaking the computer's global system. 

Run these steps in order on the new machine:

### 1. Create a New Virtual Environment
Open PowerShell inside your project folder and run:
```powershell

python -m venv venv
```

### 2. Activate It
```powershell

.\venv\Scripts\Activate.ps1
```
*(If you are on MacOS/Linux, run: `source venv/bin/activate`)*

### 3. Install All Project Dependencies
```powershell

pip install -r requirements.txt
```

### 4. Setup the Local Database
```powershell

python manage.py makemigrations
python manage.py migrate
```

### 5. Create an Admin Account (Optional)
```powershell

python manage.py createsuperuser
```

Once step 5 is done, the platform is ready! You can now use `python manage.py runserver` to bring the site online!
