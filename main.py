from flask import Flask, render_template, jsonify, request, redirect, url_for
import cx_Oracle
from datetime import datetime


cx_Oracle.init_oracle_client(lib_dir=r"E:\installuri\instantclient-basiclite-windows.x64-18.5.0.0.0dbru\instantclient_18_5")


app = Flask(__name__)



dsn = cx_Oracle.makedsn("bd-dc.cs.tuiasi.ro", 1539, service_name="orcl")
con = cx_Oracle.connect("bd119", "bd119", dsn, encoding="UTF-8")


#employees begin code
@app.route('/')
@app.route('/employees')
def emp():
	employees = []

	cur = con.cursor()
	cur.execute('select * from employees')
	for result in cur:
		employee = {}
		employee['employee_id'] = result[0]
		employee['first_name'] = result[1]
		employee['last_name'] =result[2]
		employee['email'] = result[3]
		employee['phone_number'] = result[4]

		employee['hire_date'] = datetime.strptime(str(result[5]),'%Y-%m-%d %H:%M:%S').strftime('%d.%m.%y')
		employee['job_id'] = result[6]
		employee['salary'] = result[7]
		employee['commission_pct'] = result[8]
		employee['manager_id'] = result[9]
		employee['department_id'] = result[10]
		employees.append(employee)
	cur.close()
	return render_template('employees.html', employees=employees)

#------------------
@app.route('/employees1')
def emp1():
	employees = []

	cur = con.cursor()
	cur2= con.cursor()
	cur.execute('select * from employees ')
	for result in cur:
		employee = {}
		employee['employee_id'] = result[0]
		employee['first_name'] = result[1]
		employee['last_name'] =result[2]
		employee['email'] = result[3]
		employee['phone_number'] = result[4]

		employee['hire_date'] = datetime.strptime(str(result[5]),'%Y-%m-%d %H:%M:%S').strftime('%d.%m.%y')
		employee['job_id'] = result[6]
		employee['salary'] = result[7]
		employee['commission_pct'] = result[8]
		a=0
		if result[9] != None:
			cur2.execute('select last_name from employees where employee_id='+str(result[9]))
			for res in cur2:
				employee['manager_name'] = res[0]
		if result[10] != None:
			cur2.execute('select department_name from departments where department_id='+str(result[10]))
			for res in cur2:
				employee['department_name'] = res[0]


		employees.append(employee)
	cur.close()
	return render_template('employees1.html', employees=employees)
#-----------------
@app.route('/addEmployee', methods=['GET', 'POST'])
def add_emp():
	error = None
	if request.method == 'POST':
		dep_name={}
		name="'" +request.form['department_name']+ "'"
		emp=0
		cur=con.cursor()
		cur.execute('select department_id,manager_id from departments where department_name='+name)
		for result in cur:
			dep_name['department_id']=result[0]
			dep_name['manager_id']=result[1]
		cur.close()
		cur=con.cursor()
		cur.execute('select max(employee_id) from employees')
		for result in cur:
			emp=result[0]
		cur.close()
		emp+=1
		cur = con.cursor()
		values = []
		values.append("'" + str(emp) + "'")

		values.append("'" + request.form['first_name'] + "'")
		values.append("'" + request.form['last_name'] + "'")
		values.append("'" + request.form['email'] + "'")
		values.append("'" + request.form['phone_number'] + "'")
		values.append("'" + datetime.strptime(str(request.form['hire_date']),'%d.%m.%Y').strftime('%d-%b-%y') + "'")
		values.append("'" + request.form['job_id'] + "'")
		values.append("'" + request.form['salary'] + "'")
		values.append("'" + request.form['commission_pct'] + "'")


		values.append("'" + str(dep_name['manager_id']) + "'")
		values.append("'" + str(dep_name['department_id']) + "'")

		fields = ['employee_id','first_name', 'last_name', 'email', 'phone_number', 'hire_date', 'job_id', 'salary','commission_pct','manager_id','department_id']
		query = 'INSERT INTO %s (%s) VALUES (%s)' % ('employees',', '.join(fields),', '.join(values))

		cur.execute(query)
		cur.execute('commit')
		return redirect('/employees')
	else:
		job = []
		cur = con.cursor()
		cur.execute('select job_id from Jobs')
		for result in cur:
			job.append(result[0])
		cur.close()

		dep = []
		cur = con.cursor()
		cur.execute('select department_name from departments')
		for result in cur:
			dep.append(result[0])
		cur.close()

		return render_template('addEmployee.html', Jobs=job,department=dep)


@app.route('/delEmployee', methods=['POST'])
def del_emp():
	emp = request.form['employee_id']
	cur = con.cursor()
	cur.execute('delete from employees where employee_id=' + emp)
	cur.execute('commit')
	return redirect('/employees')

@app.route('/editEmployee', methods=['POST'])
def edit_emp():
	emp=0
	dep=0
	man=0
	cur = con.cursor()

	first_name="'"+request.form['first_name']+"'"
	last_name="'"+request.form['last_name']+"'"
	cur.execute('select employee_id from employees where last_name='+last_name)
	for result in cur:
		emp=result[0]
	cur.close()

	email = "'"+request.form['email']+"'"
	phone_number =request.form['phone_number']
	hire_date = "'"+datetime.strptime(str(request.form['hire_date']),'%d.%m.%Y').strftime('%d-%b-%y')+"'"

	job_id = "'"+request.form['job_id']+"'"
	salary= request.form['salary']
	commission_pct =request.form['commission_pct']
	department_name="'"+request.form['department_name']+"'"
	cur = con.cursor()
	cur.execute('select department_id,manager_id from departments where department_name='+department_name)
	for result in cur:
		dep=result[0]
		man=result[1]
	cur.close()
	cur = con.cursor()
	query = "UPDATE employees SET first_name=%s, last_name=%s, email=%s, phone_number=%s, hire_date=%s, job_id=%s, salary=%s,commission_pct=%s,manager_id=%s,department_id=%s where employee_id=%s" % (first_name,last_name,email,phone_number,hire_date,job_id,salary,commission_pct,man,dep,emp)
	cur.execute(query)

	return redirect('/employees')

@app.route('/getEmployee', methods=['POST'])
def get_emp():
	emp = request.form['employee_id']
	cur = con.cursor()
	cur.execute('select * from employees where employee_id=' + emp)

	emps = cur.fetchone()
	employee_id=emps[0]
	first_name=emps[1]
	last_name=emps[2]
	email = emps[3]
	phone_number = emps[4]
	hire_date =datetime.strptime(str(emps[5]),'%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
	job_id = emps[6]
	salary= emps[7]
	commission_pct = emps[8]
	manager_id = emps[9]
	department_id = emps[10]
	cur.close()
	department_name=''
	cur = con.cursor()
	cur.execute('select department_name from departments where department_id='+str(department_id))
	for result in cur:
		department_name=result[0]
	cur.close()
	job = []
	cur = con.cursor()
	cur.execute('select job_id from Jobs')
	for result in cur:
		job.append(result[0])
	cur.close()
	dep = []
	cur = con.cursor()
	cur.execute('select department_name from departments')
	for result in cur:
		dep.append(result[0])
	cur.close()

	return render_template('editEmployee.html',jobs=job,job_id =job_id, department=dep,department_name=department_name, first_name=first_name,last_name=last_name,email = email,phone_number =phone_number,hire_date =hire_date,salary=salary,commission_pct =commission_pct)

#employees end code
#-----------------------------------------#
#departments start code
@app.route('/departments')
def dep():
	departments = []

	cur = con.cursor()
	cur.execute('select * from departments')
	for result in cur:
		department = {}
		department['department_id'] = result[0]
		department['department_name'] = result[1]
		department['manager_id'] =result[2]
		department['location_id'] = result[3]

		departments.append(department)
	cur.close()
	emp = []
	cur = con.cursor()
	cur.execute('select employee_id from employees')
	# import pdb;pdb.set_trace()
	for result in cur:
		emp.append(result[0])
	cur.close()

	loc = []
	cur = con.cursor()
	cur.execute('select city from locations')
	# import pdb;pdb.set_trace()
	for result in cur:
		loc.append(result[0])
	cur.close()
	return render_template('departments.html',departments=departments,employees=emp, locations=loc)

@app.route('/addDepartments', methods=['GET','POST'])
def ad_dep():
	error = None
	if request.method == 'POST':
		dep=0
		cur=con.cursor()
		cur.execute('select max(department_id) from departments')
		for result in cur:
			dep=result[0]
		cur.close()
		dep+=10
		loc=[]
		c="'" + request.form['city'] + "'"
		print(c)
		cur=con.cursor()
		cur.execute('select location_id from locations where city='+c)
		for result in cur:
			loc=result[0]
		cur.close()

		cur = con.cursor()
		values = []
		values.append("'" + str(dep)+ "'")
		values.append("'" + request.form['department_name'] + "'")
		values.append("'" + request.form['manager_id'] + "'")
		values.append("'" + str(loc) + "'")
		fields = ['department_id', 'department_name', 'manager_id', 'location_id']
		query = 'INSERT INTO %s (%s) VALUES (%s)' % (
			'departments',
			', '.join(fields),
			', '.join(values)
		)

		cur.execute(query)
		cur.execute('commit')
		return redirect('/departments')

@app.route('/delDepartments', methods=['POST'])
def del_dep():
	dep = request.form['department_id']
	cur = con.cursor()
	cur.execute('delete from departments where department_id=' + dep)
	cur.execute('commit')
	return redirect('/departments')
#departments end code
#------------------------------------------#
#jobs start code
@app.route('/jobs')
def job():
	jobs = []

	cur = con.cursor()
	cur.execute('select * from jobs')
	for result in cur:
		job = {}
		job['job_id'] = result[0]
		job['job_title'] = result[1]
		job['min_salary'] =result[2]
		job['max_salary'] = result[3]

		jobs.append(job)
	cur.close()
	return render_template('jobs.html',jobs=jobs)

@app.route('/addJob', methods=['POST'])
def ad_job():
	error = None
	if request.method == 'POST':
		cur = con.cursor()
		values = []
		values.append("'" + request.form['job_id'] + "'")
		values.append("'" + request.form['job_title'] + "'")
		values.append("'" + request.form['min_salary'] + "'")
		values.append("'" + request.form['max_salary'] + "'")
		fields = ['job_id', 'job_title', 'min_salary', 'max_salary']
		query = 'INSERT INTO %s (%s) VALUES (%s)' % (
			'jobs',
			', '.join(fields),
			', '.join(values)
		)

		cur.execute(query)
		cur.execute('commit')
		return redirect('/jobs')
@app.route('/delJob', methods=['POST'])
def del_job():
	job = "'"+request.form['job_id']+"'"
	cur = con.cursor()
	cur.execute('delete from Jobs where job_id=' + job)
	cur.execute('commit')
	return redirect('/jobs')
#jobs end code
#-------------------------------------------#
#locations start code
@app.route('/locations')
def loc():
	counselors = []

	cur = con.cursor()
	cur.execute('select * from locations')
	for result in cur:
		counselor = {}
		counselor['location_id'] = result[0]
		counselor['street_address'] = result[1]
		counselor['postal_code'] =result[2]
		counselor['city'] = result[3]
		counselor['state_province'] = result[4]
		counselor['country_id'] = result[5]

		counselors.append(counselor)
	cur.close()
	com = []
	cur = con.cursor()
	cur.execute('select country_id from countries')
	# import pdb;pdb.set_trace()
	for result in cur:
		com.append(result[0])
	cur.close()
	return render_template('locations.html',counselors=counselors,locations=com)

@app.route('/ADDlocations', methods=['POST'])
def ad_loc():
	error = None
	if request.method == 'POST':
		loc=0
		cur=con.cursor()
		cur.execute('select max(location_id) from locations')
		for result in cur:
			loc=result[0]
		cur.close()
		loc+=100
		cur = con.cursor()
		values = []
		values.append("'" + str(loc) + "'")
		values.append("'" + request.form['street_address'] + "'")
		values.append("'" + request.form['postal_code'] + "'")
		values.append("'" + request.form['city'] + "'")
		values.append("'" + request.form['state_province'] + "'")
		values.append("'" + request.form['country_id'] + "'")
		fields = ['location_id', 'street_address', 'postal_code', 'city','state_province','country_id']
		query = 'INSERT INTO %s (%s) VALUES (%s)' % (
			'locations',
			', '.join(fields),
			', '.join(values)
		)

		cur.execute(query)
		cur.execute('commit')
		return redirect('/locations')
@app.route('/delLoc', methods=['POST'])
def del_loc():
	cnp = request.form['location_id']
	cur = con.cursor()
	cur.execute('delete from locations where location_id=' + cnp)
	cur.execute('commit')
	return redirect('/locations')
#locations end code
#-----------------------------------------#
#countries start code
@app.route('/countries')
def country():
	counselors = []

	cur = con.cursor()
	cur.execute('select * from countries')
	for result in cur:
		counselor = {}
		counselor['country_id'] = result[0]
		counselor['country_name'] = result[1]
		counselor['region_id'] =result[2]
		counselors.append(counselor)
	cur.close()
	return render_template('countries.html',counselors=counselors)
@app.route('/addCountry', methods=['POST'])
def ad_count():
	error = None
	if request.method == 'POST':
		cur = con.cursor()
		values = []
		values.append("'" + request.form['country_id'] + "'")
		values.append("'" + request.form['country_name'] + "'")
		values.append("'" + request.form['region_id'] + "'")
		fields = ['country_id', 'country_name', 'region_id']
		query = 'INSERT INTO %s (%s) VALUES (%s)' % (
			'countries',
			', '.join(fields),
			', '.join(values)
		)

	cur.execute(query)
	cur.execute('commit')
	return redirect('/countries')

@app.route('/delCountry', methods=['POST'])
def del_c():
	cnp = "'"+request.form['country_id']+"'"
	cur = con.cursor()
	cur.execute('delete from countries where country_id=' + cnp)
	cur.execute('commit')
	return redirect('/countries')
#countries end code
#-----------------------------------------#
#job_grades start code
@app.route('/jobgrades')
def grades():
	counselors = []
	a=0
	cur = con.cursor()
	cur.execute('select * from job_grades')
	for result in cur:
		counselor = {}
		counselor['grade_level'] = result[0]
		counselor['lowest_sal'] = result[1]
		counselor['highest_sal'] =result[2]
		counselors.append(counselor)
	cur.close()
	#next letter
	a=ord(counselor["grade_level"])
	print(chr(a+1))
	#-------------
	return render_template('jobgrades.html',counselors=counselors)

@app.route('/addJobgrade', methods=['POST'])
def ad_grade():
	error = None
	if request.method == 'POST':
		grade=[]
		cur = con.cursor()
		cur.execute('select max(grade_level) from job_grades')
		for result in cur:
			grade=result[0]
		cur.close()
		cur = con.cursor()
		values = []
		a=ord(grade)
		print(chr(a+1))
		values.append("'" + chr(a+1) + "'")
		values.append("'" + request.form['lowest_sal'] + "'")
		values.append("'" + request.form['highest_sal'] + "'")
		fields = ['grade_level', 'lowest_sal', 'highest_sal']
		query = 'INSERT INTO %s (%s) VALUES (%s)' % (
			'job_grades',
			', '.join(fields),
			', '.join(values)
		)

		cur.execute(query)
		cur.execute('commit')
		return redirect('/jobgrades')
@app.route('/delGrade', methods=['POST'])
def del_grade():
	cnp = "'"+request.form['grade_level']+"'"
	cur = con.cursor()
	cur.execute('delete from job_grades where grade_level=' + cnp)
	cur.execute('commit')
	return redirect('/jobgrades')
#job_grades end code
#-----------------------------------------#
#job_history start code
@app.route('/jobhistory')
def history():
	counselors = []

	cur = con.cursor()
	cur.execute('select * from job_history')
	for result in cur:
		counselor = {}
		counselor['employee_id'] = result[0]
		counselor['start_date'] = datetime.strptime(str(result[1]),'%Y-%m-%d %H:%M:%S').strftime('%d-%b-%y')
		counselor['end_date'] =datetime.strptime(str(result[2]),'%Y-%m-%d %H:%M:%S').strftime('%d-%b-%y')
		counselor['job_id'] = result[3]
		counselor['department_id'] = result[4]

		counselors.append(counselor)
	cur.close()
	return render_template('jobhistory.html',counselors=counselors)
#job_history end code
#-----------------------------------------#
#regions start code
@app.route('/regions')
def regions():
	counselors = []

	cur = con.cursor()
	cur.execute('select * from regions')
	for result in cur:
		counselor = {}
		counselor['region_id'] = result[0]
		counselor['region_name'] = result[1]
		counselors.append(counselor)
	cur.close()
	return render_template('regions.html',counselors=counselors)


#regions end code
#-----------------------------------------#


#main
if __name__ == '__main__':
	app.run(debug=True)
	con.close()
