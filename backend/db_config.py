# MSSQL Connection String Configuration
# Replace the values below with your actual SQL Server details

# Option 1: SQL Server Authentication (Username/Password)
# MSSQL_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=YourDB;UID=youruser;PWD=yourpassword"

# Option 2: Windows Authentication (Integrated Security)
# MSSQL_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=YourDB;Trusted_Connection=yes"
MSSQL_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=master;Trusted_Connection=yes"

# Option 3: SQL Server Express (Local)
# MSSQL_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=YourDB;Trusted_Connection=yes"

# Option 4: Azure SQL Database
# MSSQL_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:your_server.database.windows.net,1433;DATABASE=YourDB;UID=youruser;PWD=yourpassword;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30"

# Option 5: Named Instance
# MSSQL_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\INSTANCENAME;DATABASE=YourDB;UID=youruser;PWD=yourpassword"

# Option 6: Custom Port
# MSSQL_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=YourDB;UID=youruser;PWD=yourpassword"
