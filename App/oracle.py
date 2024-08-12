import cx_Oracle

try:
	con = cx_Oracle.connect('M1198572_MM_MT1_S@/MiamiMac12@usdfw21db75v-sca.mrshmc.com')

except cx_Oracle.DatabaseError as er:
	print('There is an error in the Oracle database1:', er)

else:
	try:
		cur = con.cursor()

		# fetchall() is used to fetch all records from result set
		cur.execute('select * from company where company_id = \'18252\'')
		rows = cur.fetchall()
		print(rows)

	except cx_Oracle.DatabaseError as er:
		print('There is an error in the Oracle database2:', er)

	except Exception as er:
		print('Error:'+str(er))

	finally:
		if cur:
			cur.close()

finally:
	if con:
		con.close()
