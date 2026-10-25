/*TRANSACTIONS FILTERS*/
--QUERYS TRANSACTIONS TO MONTH
SELECT EXTRACT(DAY FROM date) AS day, SUM(amount) AS total_year FROM transactions
WHERE user_id = 0 AND EXTRACT(MONTH FROM date) = '0' AND EXTRACT(YEAR FROM date) = '0'
GROUP BY EXTRACT(DAY FROM date);	
--QUERYS TRANSACTIONS TO YEAR
SELECT TO_CHAR(date, 'month') AS month, SUM(amount) AS total FROM transactions
WHERE user_id = 0 AND EXTRACT(YEAR FROM date) = 0
GROUP BY TO_CHAR(date, 'month')
--QUERYS TRANSACTIONS ALL DATA
SELECT EXTRACT(YEAR FROM date) AS year, SUM(amount) AS total FROM transactions
WHERE user_id = 0 AND EXTRACT(YEAR FROM date)::INTEGER BETWEEN EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER - 10 AND EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER
GROUP BY EXTRACT(YEAR FROM date)

/*CATEGORIES FILTERS*/
--MONTH
SELECT c.category_name AS name, SUM(t.amount) AS value FROM transactions t
INNER JOIN categories c ON c.category_name = t.category
WHERE t.user_id = 26 AND EXTRACT(YEAR FROM t.date) = '2026' AND EXTRACT(MONTH FROM date) = '6'
GROUP BY c.category_name;
--YEAR
SELECT c.category_name AS name, SUM(t.amount) AS value FROM transactions t
INNER JOIN categories c ON c.category_name = t.category
WHERE t.user_id = 26 AND EXTRACT(YEAR FROM t.date) = '2024'
GROUP BY c.category_name;
--ALL
SELECT c.category_name AS name, SUM(t.amount) AS value FROM transactions t
INNER JOIN categories c ON c.category_name = t.category
WHERE t.user_id = 26
GROUP BY c.category_name;


/*--TOTAL BALANCE, INCOMES AND EXPENSES FILTERS*/
--ALL
SELECT SUM(amount) as total_balance, 
    (SELECT SUM(amount) FROM transactions WHERE user_id = 26 AND amount > 0) AS total_incomes,
    (SELECT SUM(amount) FROM transactions WHERE user_id = 26 AND amount < 0) AS total_expenses
FROM transactions
WHERE user_id = 26;
--YEAR
SELECT SUM(amount) as total_balance, 
	(SELECT SUM(amount) FROM transactions 
		WHERE user_id = 26 AND amount > 0 AND EXTRACT(YEAR FROM date) = '2026') AS total_incomes,
	(SELECT SUM(amount) FROM transactions 
		WHERE user_id = 26 AND amount < 0 AND EXTRACT(YEAR FROM date) = '2026') AS total_expenses
FROM transactions
WHERE user_id = 26 AND EXTRACT(YEAR FROM date) = '2026';
--MONTH
SELECT SUM(amount) as total_balance, 
	(SELECT SUM(amount) FROM transactions 
		WHERE user_id = 26 AND amount > 0 AND EXTRACT(YEAR FROM date) = '2026' AND EXTRACT(MONTH FROM date) = '10') AS total_incomes,
	(SELECT SUM(amount) FROM transactions 
		WHERE user_id = 26 AND amount < 0 AND EXTRACT(YEAR FROM date) = '2026' AND EXTRACT(MONTH FROM date) = '10') AS total_expenses
FROM transactions
WHERE user_id = 26 AND EXTRACT(YEAR FROM date) = '2026' AND EXTRACT(MONTH FROM date) = '10';

/*LAST TRANSACTIONS FILTERS*/
--ALL
SELECT id, category, type, amount FROM transactions
WHERE user_id = 26
ORDER BY date ASC LIMIT 10;
--YEAR
SELECT id, category, type, amount FROM transactions
WHERE user_id = 26 AND EXTRACT(YEAR FROM date) = '2026'
ORDER BY date ASC LIMIT 10;
--MONTH
SELECT id, category, type, amount FROM transactions
WHERE user_id = 26 AND EXTRACT(YEAR FROM date) = '2026' AND EXTRACT(MONTH FROM date) = '10'
ORDER BY date ASC LIMIT 10;
