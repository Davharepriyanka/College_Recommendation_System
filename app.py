from flask import Flask, render_template, request
import mysql.connector
import re

app = Flask(__name__)

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Priyanka@2004",
    database="capstone"
)

def extract_districts(college_names):
    districts = set()
    for name in college_names:
        match = re.search(r'([A-Za-z\s]+)$', name[0])
        if match:
            districts.add(match.group(1).strip().lower())
    return sorted(districts)

@app.route('/')
def index():
    cursor = db.cursor()
    cursor.execute("SELECT College_Name FROM college")
    college_names = cursor.fetchall()
    districts = extract_districts(college_names)
    return render_template('index.html', districts=districts) 

@app.route('/search', methods=['POST'])
def search():
    try:
        percentage = float(request.form['percentage'])
        branch = request.form['branch']
        category = request.form['category']
        district = request.form['district'].strip().lower()

        cursor = db.cursor()

        # Define the upper and lower bounds for the percentage range
        lower_bound = percentage - 3
        upper_bound = percentage + 3

        # SQL query to get 10 colleges greater than the percentage but within the upper bound (in descending order)
        query_greater = f"""
            SELECT c.College_Name, co.Course, co.{category}, c.link
            FROM courses co 
            JOIN college c ON co.College_ID = c.College_ID 
            WHERE co.Course = %s 
            AND co.{category} > %s 
            AND co.{category} <= %s 
            AND LOWER(c.College_Name) LIKE %s  
            ORDER BY co.{category} DESC  
            LIMIT 10
        """
        cursor.execute(query_greater, (branch, percentage, upper_bound, f'%{district}%'))
        greater_results = cursor.fetchall()

        # SQL query to get 10 colleges less than the percentage but within the lower bound (in descending order)
        query_lesser = f"""
            SELECT c.College_Name, co.Course, co.{category}
            FROM courses co 
            JOIN college c ON co.College_ID = c.College_ID 
            WHERE co.Course = %s 
            AND co.{category} < %s 
            AND co.{category} >= %s 
            AND LOWER(c.College_Name) LIKE %s  
            ORDER BY co.{category} DESC  
            LIMIT 10
        """
        cursor.execute(query_lesser, (branch, percentage, lower_bound, f'%{district}%'))
        lesser_results = cursor.fetchall()

        # Combine the two result sets, first greater results then lesser results
        results = greater_results + lesser_results

        # If there are fewer than 20 colleges, consider the Open category
        if len(results) < 20:
            open_category = 'GOPEN'  # Assuming 'GOPEN' is your open category
            # Query again using 'GOPEN' category
            cursor.execute(query_greater, (branch, percentage, upper_bound, f'%{district}%'))
            open_greater_results = cursor.fetchall()
            cursor.execute(query_lesser, (branch, percentage, lower_bound, f'%{district}%'))
            open_lesser_results = cursor.fetchall()

            # Append the open category results
            results += open_greater_results + open_lesser_results

        return render_template('results.html', results=results)

    except Exception as e:
        return f"An error occurred: {e}", 500


if __name__ == '__main__':
    app.run(debug=True)
