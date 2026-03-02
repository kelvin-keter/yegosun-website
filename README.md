# Yegosun Energy Website ☀️

A robust, full-stack web application built for **Yegosun Energy Limited**, a solar energy and ICT consultancy. The platform features a dynamic project portfolio, a client-facing solar ROI calculator with automated PDF reporting, and a secure administrative dashboard for content management.

## 🚀 Tech Stack

### **Backend & Logic**
* **Python / Flask**: Core application framework for handling routing and server-side logic.
* **Flask-Login**: Secure session management for the administrative dashboard.
* **Flask-Mail**: Integrated SMTP handling for automated lead notifications.
* **xhtml2pdf**: Server-side PDF generation for custom solar energy reports.

### **Frontend**
* **HTML5 / CSS3**: Responsive design tailored for a professional engineering brand.
* **Jinja2**: Dynamic templating engine for injecting database content into the UI.

### **Database & Storage**
* **PostgreSQL**: Production-grade relational database managed on Render.
* **SQLAlchemy**: ORM for seamless data manipulation and schema management.
* **Cloudinary**: Cloud-based image hosting and optimization for project and blog media.

### **Infrastructure**
* **Render**: Deployment platform for both the web service and managed database.
* **Cloudflare**: DNS management, SSL/TLS encryption, and security proxying.
* **GitHub**: Version control and CI/CD integration.

## 🛠️ Features

- **Dynamic Portfolio**: Manage and showcase solar installations with category filters.
- **Solar Calculator**: Lead generation tool that calculates estimated system size, costs, and ROI based on monthly bills.
- **Automated Reporting**: Clients receive a professional PDF report immediately after using the calculator.
- **Admin Dashboard**: Secure area to add/edit/delete blogs, services, testimonials, and projects without touching the code.
- **Lead Tracking**: Real-time database logging and email alerts for every customer inquiry.

## ⚙️ Environment Variables

To run this project, you will need to add the following variables to your environment:

`DATABASE_URL` | `SECRET_KEY` | `MAIL_USERNAME` | `MAIL_PASSWORD` | `ADMIN_EMAIL` | `CLOUDINARY_CLOUD_NAME` | `CLOUDINARY_API_KEY` | `CLOUDINARY_API_SECRET`

## 👨‍💻 Author

**Kelvin Keter** *Technopreneur & Founder*
[LinkedIn](https://www.linkedin.com/in/kelvin-keter/) | [GitHub](https://github.com/kelvin-keter) 
