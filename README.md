# Online Cinema Project

The **Online Cinema** is a web-based application built with **FastAPI** that allows users to browse, search, rate, comment, and manage their movie favorites. It also includes features for user authentication, notifications, and order system with shopping cart and payment. This project uses a modern tech stack for efficient API development and management.

---

## Features

- **Movie Management**: Browse movies, filter them by price, rating, and other criteria.
- **User Authentication**: Secure login and registration using OAuth2 with JWT tokens.
- **Comments**: Add, reply, like, and manage comments on movies.
- **Favorites**: Add and remove movies from the user's favorites list.
- **Ratings**: Rate movies on a scale from 1 to 10.
- **Notifications**: Receive notifications for updates on comments and other activities.
- **Pagination & Filtering**: Efficient pagination and filtering for large data sets.
- **Orders and Carts**: User can add movies to shopping cart and then create orders to pay for them.
- **Payment system**: User can pay for orders via Stripe

---
## Tech Stack

- **FastAPI**: Modern Python web framework for building APIs with high performance.
- **SQLAlchemy**: ORM for interacting with the database.
- **PostgreSQL**: Relational database used to store movies, comments, users, etc.
- **Pydantic**: Data validation and settings management.
- **JWT Authentication**: For secure API endpoints and user authorization.
- **Alembic**: Database migrations.
- **Background Tasks**: For handling notifications asynchronously.
---
## Getting Started
### Installation

Clone from GitHub
```shell
git clone https://github.com/dottfmar/online-cinema-fapi.git
cd online-cinema-fapi
```
Create virtual environment for Windows
```shell
python -m venv venv
venv\Scripts\activate
```
Create virtual environment for MacOS
```shell
python3 -m venv venv
source venv/bin/activate
```
Install dependencies
```shell
pip install poetry
poetry install
```
Run with Docker
```shell
cp .env.sample .env
docker-compose up --build
```
---
## Services
Web-server with documentation
```
http://127.0.0.1:8000/docs
```
Mailhog
```
http://127.0.0.1:8025/
```
Minio
```
http://127.0.0.1:9001/
```
---