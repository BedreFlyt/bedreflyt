SQL_FILES = $(wildcard *.sql)
DB_NAME = bedreflyt.db

bedreflyt.db: $(SQL_FILES)
	sqlite3 $(DB_NAME) "VACUUM;"
	@for sql_file in $(SQL_FILES); do \
		echo "Processing $$sql_file"; \
		sqlite3 $(DB_NAME) < $$sql_file; \
	done

clean:
	rm -f $(DB_NAME)
