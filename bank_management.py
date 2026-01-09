import mysql.connector

def setup_database():
    # Connect to MySQL server
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="puppy"
    )
    cursor = db.cursor()

    # Create database if not exists
    cursor.execute("CREATE DATABASE IF NOT EXISTS bank_db")
    cursor.execute("USE bank_db")

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        emp_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50),
        email VARCHAR(50) UNIQUE,
        password VARCHAR(20)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        cust_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50),
        gender VARCHAR(10),
        dob DATE,
        mobile VARCHAR(15),
        email VARCHAR(50),
        address VARCHAR(100),
        password VARCHAR(20)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_no VARCHAR(20) PRIMARY KEY,
        cust_id INT,
        account_type VARCHAR(10),
        pin VARCHAR(10),
        balance DECIMAL(10,2),
        ifsc VARCHAR(15),
        status VARCHAR(10),
        FOREIGN KEY (cust_id) REFERENCES customers(cust_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        txn_id INT AUTO_INCREMENT PRIMARY KEY,
        account_no VARCHAR(20),
        txn_type VARCHAR(10),
        amount DECIMAL(10,2),
        txn_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_no) REFERENCES accounts(account_no)
    )
    """)

    # Insert employees if empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        employees = [
            ('Admin','admin@bank.com','admin123'),
            ('Ravi','ravi@bank.com','ravi123'),
            ('Priya','priya@bank.com','priya123'),
            ('Arun','arun@bank.com','arun123'),
            ('Kavya','kavya@bank.com','kavya123'),
            ('Suresh','suresh@bank.com','suresh123'),
            ('Meena','meena@bank.com','meena123'),
            ('Vijay','vijay@bank.com','vijay123'),
            ('Anitha','anitha@bank.com','anitha123'),
            ('Karthik','karthik@bank.com','karthik123')
        ]
        cursor.executemany("INSERT INTO employees (name, email, password) VALUES (%s,%s,%s)", employees)

    # Insert customers if empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        customers = [
            ('Ramesh', 'Male', '1990-01-12', '9000000001', 'ramesh@gmail.com', 'Chennai', 'ramesh123'),
            ('Sita', 'Female', '1992-02-10', '9000000002', 'sita@gmail.com', 'Salem', 'sita123'),
            ('Kumar', 'Male', '1989-03-15', '9000000003', 'kumar@gmail.com', 'Erode', 'kumar123'),
            ('Lakshmi', 'Female', '1991-04-18', '9000000004', 'lakshmi@gmail.com', 'Madurai', 'lakshmi123'),
            ('Arun', 'Male', '1988-05-20', '9000000005', 'arun@gmail.com', 'Coimbatore', 'arun123'),
            ('Divya', 'Female', '1993-06-22', '9000000006', 'divya@gmail.com', 'Trichy', 'divya123'),
            ('Mani', 'Male', '1990-07-25', '9000000007', 'mani@gmail.com', 'Karur', 'mani123'),
            ('Priya', 'Female', '1992-08-28', '9000000008', 'priya@gmail.com', 'Namakkal', 'priya123'),
            ('Vimal', 'Male', '1987-09-30', '9000000009', 'vimal@gmail.com', 'Salem', 'vimal123'),
            ('Anu', 'Female', '1994-10-02', '9000000010', 'anu@gmail.com', 'Chennai', 'anu123'),
            ('Sathish', 'Male', '1989-11-05', '9000000011', 'sathish@gmail.com', 'Erode', 'sathish123'),
            ('Pooja', 'Female', '1991-12-07', '9000000012', 'pooja@gmail.com', 'Coimbatore', 'pooja123'),
            ('Gopi', 'Male', '1988-01-09', '9000000013', 'gopi@gmail.com', 'Madurai', 'gopi123'),
            ('Meena', 'Female', '1992-02-11', '9000000014', 'meena@gmail.com', 'Trichy', 'meena123'),
            ('Raj', 'Male', '1990-03-13', '9000000015', 'raj@gmail.com', 'Salem', 'raj123'),
            ('Kavitha', 'Female', '1993-04-15', '9000000016', 'kavitha@gmail.com', 'Karur', 'kavitha123'),
            ('Naveen', 'Male', '1987-05-17', '9000000017', 'naveen@gmail.com', 'Namakkal', 'naveen123'),
            ('Keerthi', 'Female', '1994-06-19', '9000000018', 'keerthi@gmail.com', 'Chennai', 'keerthi123'),
            ('Ajay', 'Male', '1989-07-21', '9000000019', 'ajay@gmail.com', 'Erode', 'ajay123'),
            ('Sandhya', 'Female', '1991-08-23', '9000000020', 'sandhya@gmail.com', 'Madurai', 'sandhya123'),
            ('Prakash', 'Male', '1990-09-25', '9000000021', 'prakash@gmail.com', 'Salem', 'prakash123'),
            ('Revathi', 'Female', '1992-10-27', '9000000022', 'revathi@gmail.com', 'Trichy', 'revathi123'),
            ('Bala', 'Male', '1988-11-29', '9000000023', 'bala@gmail.com', 'Coimbatore', 'bala123'),
            ('Malar', 'Female', '1993-12-01', '9000000024', 'malar@gmail.com', 'Karur', 'malar123'),
            ('Surya', 'Male', '1989-01-03', '9000000025', 'surya@gmail.com', 'Namakkal', 'surya123'),
            ('Nisha', 'Female', '1994-02-05', '9000000026', 'nisha@gmail.com', 'Chennai', 'nisha123'),
            ('Ravi', 'Male', '1990-03-07', '9000000027', 'ravi@gmail.com', 'Erode', 'ravi123'),
            ('Aishwarya', 'Female', '1992-04-09', '9000000028', 'aishu@gmail.com', 'Salem', 'aishwarya123'),
            ('Kannan', 'Male', '1987-05-11', '9000000029', 'kannan@gmail.com', 'Madurai', 'kannan123'),
            ('Deepa', 'Female', '1993-06-13', '9000000030', 'deepa@gmail.com', 'Trichy', 'deepa123'),
            ('Mohan', 'Male', '1988-07-15', '9000000031', 'mohan@gmail.com', 'Coimbatore', 'mohan123'),
            ('Sindhu', 'Female', '1991-08-17', '9000000032', 'sindhu@gmail.com', 'Karur', 'sindhu123'),
            ('Raghav', 'Male', '1990-09-19', '9000000033', 'raghav@gmail.com', 'Namakkal', 'raghav123'),
            ('Bhavya', 'Female', '1994-10-21', '9000000034', 'bhavya@gmail.com', 'Chennai', 'bhavya123'),
            ('Sanjay', 'Male', '1989-11-23', '9000000035', 'sanjay@gmail.com', 'Erode', 'sanjay123'),
            ('Pavithra', 'Female', '1992-12-25', '9000000036', 'pavi@gmail.com', 'Salem', 'pavithra123'),
            ('Vignesh', 'Male', '1987-01-27', '9000000037', 'vignesh@gmail.com', 'Madurai', 'vignesh123'),
            ('Harini', 'Female', '1993-02-28', '9000000038', 'harini@gmail.com', 'Trichy', 'harini123'),
            ('Ashok', 'Male', '1990-03-30', '9000000039', 'ashok@gmail.com', 'Coimbatore', 'ashok123'),
            ('Swathi', 'Female', '1994-04-01', '9000000040', 'swathi@gmail.com', 'Karur', 'swathi123')
        ]

        cursor.executemany(
            "INSERT INTO customers (name, gender, dob, mobile, email, address, password) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            customers
        )

    db.commit()
    db.close()
    print("Database setup completed with unique passwords for all customers.")

# Call setup
setup_database()
