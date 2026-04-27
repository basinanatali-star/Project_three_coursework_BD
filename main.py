import csv
import psycopg2


def fill_table_from_csv(cursor, table_name, file_name, column_names):

    with open(file_name, newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.reader(csvfile)
        next(csv_reader)

        data = []
        for row in csv_reader:
            if len(row) == len(column_names):
                data.append(row)

        query = f"INSERT INTO {table_name} ({", ".join(column_names)}) VALUES ({', '.join(["%s"] * len(column_names))})"

        cursor.executemany(query, data)


def main():

     conn = psycopg2.connect(
         host="localhost",
         port=5432,
         dbname="bddz",
         user="postgres",
         password=12061977,
     )
     cursor = conn.cursor()

     fill_table_from_csv(cursor,'customers', 'data/customers_data.csv', ['customer_id', 'company_name', 'contact_name'])
     fill_table_from_csv(cursor, 'employees', 'data/employees_data.csv', ['employee_id', 'first_name', 'last_name', 'title', 'birth_date', 'notes'])
     fill_table_from_csv(cursor, 'orders', 'data/orders_data.csv', ['order_id', 'customer_id', 'employee_id', 'order_date', 'ship_city'])

     conn.commit()
     cursor.close()
     conn.close()

if __name__ == "__main__":
    main()
