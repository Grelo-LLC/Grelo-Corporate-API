# Grelo Korporativ API

## Django Layihəsinin Quraşdırılması və İstifadəsi üzrə Təlimat

Bu sənəd, Django layihəsinin quraşdırılması, virtual mühitin yaradılması, asılılıqların qurulması və layihənin işə salınması üçün addım-addım təlimatları təqdim edir.

## Tələblər

Aşağıdakı proqramlar kompüterinizdə quraşdırılmış olmalıdır:

- **pip (Python paket meneceri)**
- **Virtualenv (və ya digər virtual mühit meneceri)**
- **Git (layihəni klonlamaq üçün)**

## Layihənin Quraşdırılması

### 1. Layihəni Git ilə Endirmək

Əvvəlcə layihəni Git istifadə edərək kompüterinizə klonlayın:

```bash
git clone https://github.com/Grelo-LLC/Grelo-Corporate-API.git
```

<br>

### 2. Virtual Mühit Yaratmaq

#### MacOS / Linux:

```bash
python3 -m venv env
source env/bin/activate
```

#### Windows:

```bash
py -m venv env
.\env\Scripts\activate
```

<br>

### 3. Lazımi Paketləri Qurmaq

```bash
pip install -r requirements.txt
```

<br>

### 4. Migrasiyaları Tətbiq Etmək

#### MacOS / Linux:

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

#### Windows:

```bash
py manage.py makemigrations
py manage.py migrate
```

<br>

### 5. Superuser (İnzibatçı) Yaratmaq

#### MacOS / Linux:

```bash
python3 manage.py createsuperuser
```

#### Windows:

```bash
py manage.py createsuperuser
```

<br>

### 6. Statik Faylları Yığmaq

#### MacOS / Linux:

```bash
python3 manage.py collectstatic
```

#### Windows:

```bash
py manage.py collectstatic
```

<br>

### 7. Layihəni İşə Salmaq

#### MacOS / Linux:

```bash
python3 manage.py runserver
```

#### Windows:

```bash
py manage.py runserver
```

<br>

### Bu `README.md` faylı layihəni qurmaq və işə salmaq üçün bütün lazım olan addımları təqdim edir. Başqasına layihəni asanlıqla quraşdırmağa kömək edəcək.