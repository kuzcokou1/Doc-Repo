CREATE TABLE users (
	uid serial PRIMARY KEY,
	fname varchar(256) not null,
	lname varchar(256) not null,
	username varchar(256) not null,
	email varchar(256) not null,
	pwd varchar(256) not null
);