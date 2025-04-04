from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
from datetime import timedelta
from fpdf import FPDF
import os
import logging
import io
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'school_results'
mysql = MySQL(app)

class AcademicReport(FPDF):
    def header(self):
        self.image('static/images/headerr.jpg', 10, 8, 25)
        self.set_font('Arial', 'B', 14)
        self.set_y(10)
        self.cell(0, 5, 'Pindeniya National School', 0, 1, 'R')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Pindeniya, Kegalle', 0, 1, 'R')
        self.cell(0, 5, 'Phone: (94)352289028 | Email: pindeniyacollege@gmail.com', 0, 1, 'R')
        self.set_y(40)
        self.set_font('Arial', 'B', 18)
        self.set_text_color(0, 0, 128)
        self.cell(0, 10, 'ACADEMIC PERFORMANCE REPORT', 0, 1, 'C')
        self.line(10, 50, 200, 50)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.line(10, self.get_y(), 200, self.get_y())
        self.cell(0, 10, f'Page {self.page_no()} | Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

# Login Routes
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM sms_user WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['u_id']
            session['name'] = user['first_name']
            session['email'] = user['email']
            app.logger.debug(f"Session set for user: {user['email']}")  # Debug log
            app.secret_key = 'CBBYBWA'  # Must be set!
            app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Extend session
            app.config['SESSION_COOKIE_SECURE'] = True  # If using HTTPS
            app.config['SESSION_COOKIE_HTTPONLY'] = True
            app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevents CSRF
            mesage = 'Logged in successfully!'
            return redirect(url_for('dashboard'))
        else:
            mesage = 'Please enter correct email / password!'
    return render_template('login.html', mesage=mesage)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

# Dashboard Route
@app.route("/dashboard")
def dashboard():
    if 'loggedin' in session:
        return render_template("dashboard.html")
    return redirect(url_for('login'))

# Student Routes
@app.route("/student")
def student():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM sms_students ORDER BY class_id, name')
        students = cursor.fetchall()
        return render_template("student.html", students=students)
    return redirect(url_for('login'))

@app.route("/edit_student", methods=['GET'])
def edit_student():
    if 'loggedin' in session:
        student_id = request.args.get('student_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get student data
        cursor.execute('SELECT * FROM sms_students WHERE student_id = %s', (student_id,))
        student = cursor.fetchone()
        
        # Get classes for dropdown
        cursor.execute('SELECT * FROM sms_classes ORDER BY name')
        classes = cursor.fetchall()
        
        return render_template("edit_student.html", student=student, classes=classes)
    return redirect(url_for('login'))

@app.route("/delete_student", methods=['GET'])
def delete_student():
    if 'loggedin' in session:
        student_id = request.args.get('student_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM sms_students WHERE student_id = %s', (student_id,))
        mysql.connection.commit()
        return redirect(url_for('student'))
    return redirect(url_for('login'))

@app.route("/save_student", methods=['POST'])
def save_student():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if request.method == 'POST' and 'name' in request.form and 'class_id' in request.form:
            student_id = request.form['student_id']
            name = request.form['name']
            class_id = request.form['class_id']
            action = request.form['action']

            if action == 'update':
                cursor.execute('UPDATE sms_students SET name = %s, class_id = %s WHERE student_id = %s', 
                             (name, class_id, student_id))
            else:
                cursor.execute('INSERT INTO sms_students (student_id, name, class_id) VALUES (%s, %s, %s)',
                             (student_id, name, class_id))
            mysql.connection.commit()
        return redirect(url_for('student'))
    return redirect(url_for('login'))

@app.route("/student_report", methods=['GET'])
def student_report():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        try:
            # Get all classes for dropdown
            cursor.execute('SELECT * FROM sms_classes ORDER BY name')
            classes = cursor.fetchall()
            
            selected_student = request.args.get('student_id')
            selected_year = request.args.get('year', datetime.now().year)  # Default to current year
            student_data = None
            marks_data = []
            class_rank = "N/A"
            
            if selected_student:
                # Get student information
                cursor.execute('''
                    SELECT s.*, c.name as class_name 
                    FROM sms_students s
                    JOIN sms_classes c ON s.class_id = c.class_id
                    WHERE s.student_id = %s
                ''', (selected_student,))
                student_data = cursor.fetchone()
                
                if student_data:
                    # THIS IS WHERE YOUR QUERY GOES:
                    cursor.execute('''
                        SELECT m.*, sub.subject 
                        FROM sms_marks m
                        JOIN sms_subjects sub ON m.subject_id = sub.subject_id
                        WHERE m.student_id = %s AND m.year = %s
                        ORDER BY m.term, sub.subject
                    ''', (selected_student, selected_year))
                    marks_data = cursor.fetchall()
                    
                    # Calculate class rank for the selected year
                    cursor.execute('''
                        SELECT m.student_id, AVG(m.marks) as avg_mark,
                               RANK() OVER (ORDER BY AVG(m.marks) DESC) as rank
                        FROM sms_marks m
                        JOIN sms_students s ON m.student_id = s.student_id
                        WHERE s.class_id = %s AND m.year = %s
                        GROUP BY m.student_id
                    ''', (student_data['class_id'], selected_year))
                    rankings = cursor.fetchall()
                    
                    for rank in rankings:
                        if rank['student_id'] == selected_student:
                            class_rank = rank['rank']
                            break
            
            # Get students for the selected class
            class_id = request.args.get('class_id')
            students = get_students_by_class(cursor, class_id) if class_id else []
            
            # Get available years for dropdown
            cursor.execute('SELECT DISTINCT year FROM sms_marks ORDER BY year DESC')
            available_years = [str(year['year']) for year in cursor.fetchall()]
            
            return render_template("student_report.html", 
                                classes=classes,
                                students=students,
                                selected_student=selected_student,
                                selected_year=selected_year,
                                available_years=available_years,
                                student_data=student_data,
                                marks_data=marks_data,
                                class_rank=class_rank)
        
        except Exception as e:
            app.logger.error(f"Error in student_report: {str(e)}")
            flash('An error occurred while generating the report', 'danger')
            return redirect(url_for('dashboard'))
        
        finally:
            cursor.close()
    
    return redirect(url_for('login'))
def get_students_by_class(cursor, class_id):
    """Helper function to get students by class ID"""
    if not class_id:
        return []
    
    try:
        cursor.execute('''
            SELECT student_id, name 
            FROM sms_students 
            WHERE class_id = %s 
            ORDER BY name
        ''', (class_id,))
        return cursor.fetchall()
    except Exception as e:
        app.logger.error(f"Error getting students by class: {str(e)}")
        return []


@app.route('/get_students')
def get_students():
    if 'loggedin' in session:
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({'error': 'Class ID is required'}), 400
            
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('''
                SELECT s.student_id, s.name, c.name as class_name 
                FROM sms_students s
                JOIN sms_classes c ON s.class_id = c.class_id
                WHERE s.class_id = %s
                ORDER BY s.name
            ''', (class_id,))
            
            students = cursor.fetchall()
            return jsonify(students)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
    return jsonify({'error': 'Unauthorized'}), 401


@app.route('/marks')
def marks():
    if 'loggedin' not in session:
        flash('Please login to access this page', 'danger')
        return redirect(url_for('login'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get all classes
        cursor.execute('SELECT class_id, name FROM sms_classes ORDER BY name')
        classes = cursor.fetchall()
        
        # Get all subjects
        cursor.execute('SELECT subject_id, subject FROM sms_subjects ORDER BY subject')
        subjects = cursor.fetchall()
        
        return render_template("marks.html",
                            classes=classes,
                            subjects=subjects,
                            current_year=datetime.now().year)
        
    except Exception as e:
        app.logger.error(f"Database error in marks route: {str(e)}")
        flash('Error loading marks page', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
    

@app.route('/input_marks', methods=['POST'])
def input_marks():
    if 'loggedin' in session:
        try:
            # Get form data
            student_id = request.form['student']
            subject_id = request.form['subject']
            marks = float(request.form['marks'])
            term = request.form['term']
            year = request.form['year']
            
            # Validate marks
            if marks < 0 or marks > 100:
                return jsonify({'success': False, 'error': 'Marks must be between 0-100'})
            
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('''
                INSERT INTO sms_marks 
                (student_id, subject_id, term, marks, year) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (student_id, subject_id, term, marks, year))
            
            mysql.connection.commit()
            return jsonify({'success': True, 'message': 'Marks saved successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
        finally:
            cursor.close()
    return jsonify({'success': False, 'error': 'Unauthorized'}), 401

@app.route("/generate_student_report", methods=['GET', 'POST'])
def generate_student_report():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            student_id = request.form.get('student_id')
            class_id = request.form.get('class_id', '')
        else:  # GET request
            student_id = request.args.get('student_id')
            class_id = request.args.get('class_id', '')

        if not student_id:
            flash('Student ID is required', 'danger')
            return redirect(request.referrer or url_for('dashboard'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get student information
        cursor.execute('''
            SELECT s.*, c.name as class_name 
            FROM sms_students s
            JOIN sms_classes c ON s.class_id = c.class_id
            WHERE s.student_id = %s
        ''', (student_id,))
        student_data = cursor.fetchone()
        
        if not student_data:
            flash('Student not found', 'danger')
            return redirect(request.referrer or url_for('dashboard'))
        
        # Get all marks for the student (current year)
        cursor.execute('''
            SELECT m.*, sub.subject 
            FROM sms_marks m
            JOIN sms_subjects sub ON m.subject_id = sub.subject_id
            WHERE m.student_id = %s AND m.year = YEAR(CURDATE())
            ORDER BY m.term, sub.subject
        ''', (student_id,))
        marks_data = cursor.fetchall()
        
        # Calculate class rank
        cursor.execute('''
            SELECT student_id, AVG(marks) as avg_mark,
                   RANK() OVER (ORDER BY AVG(marks) DESC) as rank
            FROM sms_marks
            WHERE class_id = %s AND year = YEAR(CURDATE())
            GROUP BY student_id
        ''', (student_data['class_id'],))
        rankings = cursor.fetchall()
        
        class_rank = "N/A"
        for rank in rankings:
            if rank['student_id'] == student_id:
                class_rank = rank['rank']
                break
        
        # Calculate term averages
        term_averages = {}
        for mark in marks_data:
            term = mark['term']
            if term not in term_averages:
                term_averages[term] = {'total': 0, 'count': 0}
            term_averages[term]['total'] += mark['marks']
            term_averages[term]['count'] += 1
        
        for term in term_averages:
            term_averages[term] = term_averages[term]['total'] / term_averages[term]['count']
        
        # Generate PDF
        pdf = AcademicReport()
        pdf.add_page()
        
        # Report Header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f"Student Performance Report", 0, 1, 'C')
        pdf.ln(10)
        
        # Student Information
        pdf.set_font('Arial', '', 12)
        pdf.cell(40, 10, "Student ID:", 0)
        pdf.cell(0, 10, student_data['student_id'], 0, 1)
        pdf.cell(40, 10, "Name:", 0)
        pdf.cell(0, 10, student_data['name'], 0, 1)
        pdf.cell(40, 10, "Class:", 0)
        pdf.cell(0, 10, student_data['class_name'], 0, 1)
        pdf.cell(40, 10, "Class Rank:", 0)
        pdf.cell(0, 10, str(class_rank), 0, 1)
        pdf.ln(15)
        
        # Marks Table Header
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(70, 10, "Subject", 1, 0, 'C')
        pdf.cell(30, 10, "Term", 1, 0, 'C')
        pdf.cell(30, 10, "Marks", 1, 0, 'C')
        pdf.cell(0, 10, "Grade", 1, 1, 'C')
        
        # Marks Data
        pdf.set_font('Arial', '', 10)
        for mark in marks_data:
            pdf.cell(70, 10, mark['subject'], 1)
            pdf.cell(30, 10, f"Term {mark['term']}", 1)
            pdf.cell(30, 10, str(mark['marks']), 1)
            pdf.cell(0, 10, get_grade(mark['marks']), 1, 1)
        
        pdf.ln(10)
        
        # Term Averages
        if term_averages:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "Term Averages:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            for term, avg in term_averages.items():
                pdf.cell(40, 10, f"Term {term}:", 0)
                pdf.cell(30, 10, f"{avg:.2f}", 0)
                pdf.cell(0, 10, get_grade(avg), 0, 1)
        
        # Save PDF to memory
        pdf_output = pdf.output(dest='S').encode('latin1')
        
        # Create response
        response = make_response(pdf_output)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = \
            f'attachment; filename=Student_Report_{student_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error generating report: {str(e)}")
        flash('Error generating report', 'danger')
        return redirect(request.referrer or url_for('dashboard'))
    finally:
        cursor.close()

def get_grade(marks):
    if marks is None:
        return "N/A"
    if marks >= 75:
        return "A"
    elif marks >= 65:
        return "B"
    elif marks >= 50:
        return "C"
    elif marks >= 35:
        return "S"
    else:
        return "F"

# Teacher Routes
@app.route("/teacher")
def teacher():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT t.*, s.subject FROM sms_teacher t JOIN sms_subjects s ON t.subject_code = s.code')
        teachers = cursor.fetchall()
        return render_template("teacher.html", teachers=teachers)
    return redirect(url_for('login'))

@app.before_request
def check_session():
    if request.endpoint != 'login' and 'loggedin' not in session:
        return redirect(url_for('login'))

@app.route("/edit_teacher", methods=['GET'])
def edit_teacher():
    if 'loggedin' in session:
        teacher_id = request.args.get('teacher_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get teacher data
        cursor.execute('SELECT * FROM sms_teacher WHERE teacher_id = %s', (teacher_id,))
        teacher = cursor.fetchone()
        
        # Get subjects for dropdown
        cursor.execute('SELECT * FROM sms_subjects ORDER BY subject')
        subjects = cursor.fetchall()
        
        return render_template("edit_teacher.html", teacher=teacher, subjects=subjects)
    return redirect(url_for('login'))

@app.route("/save_teacher", methods=['POST'])
def save_teacher():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if request.method == 'POST' and 'name' in request.form and 'subject_code' in request.form:
            teacher_id = request.form['teacher_id']
            name = request.form['name']
            subject_code = request.form['subject_code']
            action = request.form['action']

            if action == 'update':
                cursor.execute('UPDATE sms_teacher SET name = %s, subject_code = %s WHERE teacher_id = %s', 
                             (name, subject_code, teacher_id))
            else:
                cursor.execute('INSERT INTO sms_teacher (teacher_id, name, subject_code) VALUES (%s, %s, %s)',
                             (teacher_id, name, subject_code))
            mysql.connection.commit()
        return redirect(url_for('teacher'))
    return redirect(url_for('login'))

@app.route("/delete_teacher", methods=['GET'])
def delete_teacher():
    if 'loggedin' in session:
        teacher_id = request.args.get('teacher_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM sms_teacher WHERE teacher_id = %s', (teacher_id,))
        mysql.connection.commit()
        return redirect(url_for('teacher'))
    return redirect(url_for('login'))

# Subject Routes
@app.route("/subject")
def subjects():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM sms_subjects ORDER BY subject')
        subjects = cursor.fetchall()
        return render_template("subject.html", subjects=subjects)
    return redirect(url_for('login'))

@app.route("/edit_subject", methods=['GET'])
def edit_subject():
    if 'loggedin' in session:
        subject_id = request.args.get('subject_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM sms_subjects WHERE subject_id = %s', (subject_id,))
        subject = cursor.fetchone()
        return render_template("edit_subject.html", subject=subject)
    return redirect(url_for('login'))

@app.route("/save_subject", methods=['POST'])
def save_subject():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if request.method == 'POST' and 'subject' in request.form and 'code' in request.form:
            subject_id = request.form.get('subject_id')
            subject = request.form['subject']
            code = request.form['code']
            action = request.form['action']

            if action == 'update':
                cursor.execute('''
                    UPDATE sms_subjects 
                    SET subject = %s, code = %s 
                    WHERE subject_id = %s
                ''', (subject, code, subject_id))
            else:
                cursor.execute('''
                    INSERT INTO sms_subjects (subject_id, subject, code)
                    VALUES (%s, %s, %s)
                ''', (subject_id, subject, code))
            mysql.connection.commit()
        return redirect(url_for('subjects'))
    return redirect(url_for('login'))

@app.route("/delete_subject", methods=['GET'])
def delete_subject():
    if 'loggedin' in session:
        subject_id = request.args.get('subject_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM sms_subjects WHERE subject_id = %s', (subject_id,))
        mysql.connection.commit()
        return redirect(url_for('subjects'))
    return redirect(url_for('login'))

# Result Analysis Routes
@app.route("/results")
def results():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM sms_classes ORDER BY name')
        classes = cursor.fetchall()
        
        selected_class = request.args.get('class_id')
        results_data = []
        
        if selected_class:
            # Get class average and rank
            cursor.execute('''
                SELECT s.student_id, s.name, 
                       AVG(m.marks) as average,
                       RANK() OVER (ORDER BY AVG(m.marks) DESC) as rank
                FROM sms_marks m
                JOIN sms_students s ON m.student_id = s.student_id
                WHERE s.class_id = %s AND m.year = YEAR(CURDATE())
                GROUP BY s.student_id, s.name
                ORDER BY rank
            ''', (selected_class,))
            results_data = cursor.fetchall()
            
            # Get subject marks for each student
            for student in results_data:
                cursor.execute('''
                    SELECT sub.subject, m.term, m.marks 
                    FROM sms_marks m
                    JOIN sms_subjects sub ON m.subject_id = sub.subject_id
                    WHERE m.student_id = %s AND m.year = YEAR(CURDATE())
                    ORDER BY sub.subject, m.term
                ''', (student['student_id'],))
                student['marks'] = cursor.fetchall()
        
        return render_template("results.html", 
                            classes=classes,
                            selected_class=selected_class,
                            results_data=results_data)
    return redirect(url_for('login'))

@app.route('/generate_report', methods=['POST'])
def generate_report():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    class_id = request.form.get('class_id')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get class name
    cursor.execute('SELECT name FROM sms_classes WHERE class_id = %s', (class_id,))
    class_info = cursor.fetchone()
    if not class_info:
        return "Class not found", 404
    
    # Get student results (same query as in results route)
    cursor.execute('''
        SELECT s.student_id, s.name, 
               AVG(m.marks) as average,
               RANK() OVER (ORDER BY AVG(m.marks) DESC) as rank
        FROM sms_marks m
        JOIN sms_students s ON m.student_id = s.student_id
        WHERE s.class_id = %s AND m.year = YEAR(CURDATE())
        GROUP BY s.student_id, s.name
        ORDER BY rank
    ''', (class_id,))
    results_data = cursor.fetchall()
    
    if not results_data:
        return "No results available for this class", 400
    
    # Get subject marks for each student
    for student in results_data:
        cursor.execute('''
            SELECT sub.subject, m.term, m.marks 
            FROM sms_marks m
            JOIN sms_subjects sub ON m.subject_id = sub.subject_id
            WHERE m.student_id = %s AND m.year = YEAR(CURDATE())
            ORDER BY sub.subject, m.term
        ''', (student['student_id'],))
        student['marks'] = cursor.fetchall()
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Report Header
    elements.append(Paragraph(f"Class Performance Report", styles['Title']))
    elements.append(Paragraph(f"Class: {class_info['name']}", styles['Heading2']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 24))
    
    # Summary Table
    summary_data = [['Rank', 'Student Name', 'Average Score']]
    for student in results_data:
        summary_data.append([
            str(student['rank']),
            student['name'],
            f"{student['average']:.2f}"
        ])
    
    summary_table = Table(summary_data, colWidths=[50, 300, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D9E1F2')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))
    
    # Detailed Marks Section
    elements.append(Paragraph("Detailed Marks Breakdown", styles['Heading2']))
    
    for student in results_data:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Student: {student['name']} (Rank: {student['rank']}, Average: {student['average']:.2f})", 
                                styles['Heading3']))
        
        # Group marks by term
        terms = sorted(list(set(mark['term'] for mark in student['marks'])))
        
        for term in terms:
            term_marks = [m for m in student['marks'] if m['term'] == term]
            term_data = [['Subject', 'Marks']]
            for mark in term_marks:
                term_data.append([mark['subject'], str(mark['marks'])])
            
            term_table = Table(term_data, colWidths=[200, 100])
            term_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E2EFDA')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(Paragraph(f"Term {term}", styles['Normal']))
            elements.append(term_table)
            elements.append(Spacer(1, 8))
    
    # Build PDF
    doc.build(elements)
    
    # Prepare response
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={class_info["name"].replace(" ", "_")}_Performance_Report.pdf'
    
    return response

@app.route("/class_report")
def class_report():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get all classes for dropdown
        cursor.execute('SELECT * FROM sms_classes ORDER BY name')
        classes = cursor.fetchall()
        
        selected_class = request.args.get('class_id')
        class_data = None
        students_data = []
        subject_averages = []
        
        if selected_class:
            # Get class information with section
            cursor.execute('''
                SELECT c.*, s.section 
                FROM sms_classes c
                JOIN sms_section s ON c.section_id = s.section_id
                WHERE c.class_id = %s
            ''', (selected_class,))
            class_data = cursor.fetchone()
            
            if class_data:
                # Get all students with their average marks and rank
                cursor.execute('''
                    SELECT s.student_id, s.name, 
                           AVG(m.marks) as average,
                           RANK() OVER (ORDER BY AVG(m.marks) DESC) as rank
                    FROM sms_students s
                    LEFT JOIN sms_marks m ON s.student_id = m.student_id
                    WHERE s.class_id = %s AND m.year = YEAR(CURDATE())
                    GROUP BY s.student_id, s.name
                    ORDER BY rank
                ''', (selected_class,))
                students_data = cursor.fetchall()
                
                # Get subject-wise averages for the class
                cursor.execute('''
                    SELECT sub.subject_id, sub.subject, 
                           AVG(m.marks) as class_avg
                    FROM sms_marks m
                    JOIN sms_subjects sub ON m.subject_id = sub.subject_id
                    JOIN sms_students s ON m.student_id = s.student_id
                    WHERE s.class_id = %s AND m.year = YEAR(CURDATE())
                    GROUP BY sub.subject_id, sub.subject
                ''', (selected_class,))
                subject_averages = cursor.fetchall()
        
        return render_template("class_report.html", 
                            classes=classes,
                            selected_class=selected_class,
                            class_data=class_data,
                            students_data=students_data,
                            subject_averages=subject_averages)
    return redirect(url_for('login'))

@app.route("/generate_class_report", methods=['GET', 'POST'])
def generate_class_report():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            class_id = request.form.get('class_id')
        else:
            class_id = request.args.get('class_id')

        if not class_id:
            flash('Class ID is required', 'danger')
            return redirect(request.referrer or url_for('dashboard'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get class information
        cursor.execute('''
            SELECT c.*, s.section 
            FROM sms_classes c
            JOIN sms_section s ON c.section_id = s.section_id
            WHERE c.class_id = %s
        ''', (class_id,))
        class_data = cursor.fetchone()
        
        if not class_data:
            flash('Class not found', 'danger')
            return redirect(request.referrer or url_for('dashboard'))
        
        # Get all students with their average marks and rank
        cursor.execute('''
            SELECT s.student_id, s.name, 
                   AVG(m.marks) as average,
                   RANK() OVER (ORDER BY AVG(m.marks) DESC) as rank
            FROM sms_students s
            LEFT JOIN sms_marks m ON s.student_id = m.student_id
            WHERE s.class_id = %s AND m.year = YEAR(CURDATE())
            GROUP BY s.student_id, s.name
            ORDER BY rank
        ''', (class_id,))
        students_data = cursor.fetchall()
        
        # Get subject-wise averages for the class
        cursor.execute('''
            SELECT sub.subject_id, sub.subject, 
                   AVG(m.marks) as class_avg
            FROM sms_marks m
            JOIN sms_subjects sub ON m.subject_id = sub.subject_id
            JOIN sms_students s ON m.student_id = s.student_id
            WHERE s.class_id = %s AND m.year = YEAR(CURDATE())
            GROUP BY sub.subject_id, sub.subject
        ''', (class_id,))
        subject_averages = cursor.fetchall()
        
        # Generate PDF
        pdf = AcademicReport()
        pdf.add_page()
        
        # PDF Header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f"Class Performance Report - {class_data['name']} ({class_data['section']})", 0, 1, 'C')
        pdf.ln(10)
        
        # Class Information
        pdf.set_font('Arial', '', 12)
        pdf.cell(40, 10, "Class:", 0)
        pdf.cell(0, 10, f"{class_data['name']} ({class_data['section']})", 0, 1)
        pdf.cell(40, 10, "Total Students:", 0)
        pdf.cell(0, 10, str(len(students_data)), 0, 1)
        pdf.ln(10)
        
        # Subject Averages
        if subject_averages:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "Subject Averages:", 0, 1)
            
            pdf.set_font('Arial', '', 10)
            for subject in subject_averages:
                pdf.cell(60, 10, subject['subject'], 0)
                pdf.cell(30, 10, f"{subject['class_avg']:.2f}", 0)
                pdf.cell(0, 10, get_grade(subject['class_avg']), 0, 1)
            
            pdf.ln(10)
        
        # Student Performance
        if students_data:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(25, 10, "Rank", 1, 0, 'C')
            pdf.cell(60, 10, "Student", 1, 0, 'C')
            pdf.cell(35, 10, "Average", 1, 0, 'C')
            pdf.cell(0, 10, "Grade", 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            for student in students_data:
                pdf.cell(25, 10, str(student['rank']), 1, 0, 'C')
                pdf.cell(60, 10, student['name'], 1)
                pdf.cell(35, 10, f"{student['average']:.2f}", 1, 0, 'C')
                pdf.cell(0, 10, get_grade(student['average']), 1, 0, 'C')
                pdf.ln()
        
        # Save PDF to memory
        pdf_output = pdf.output(dest='S').encode('latin1')
        
        # Create response
        response = make_response(pdf_output)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = \
            f'attachment; filename=Class_Report_{class_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error generating class report: {str(e)}")
        flash('Error generating report', 'danger')
        return redirect(request.referrer or url_for('dashboard'))
    finally:
        cursor.close()

def get_grade(marks):
    if marks is None:
        return "N/A"
    if marks >= 75:
        return "A"
    elif marks >= 65:
        return "B"
    elif marks >= 50:
        return "C"
    elif marks >= 35:
        return "S"
    else:
        return "F"

if __name__ == "__main__":
    app.run(debug=True)