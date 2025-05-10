CREATE TABLE IF NOT EXISTS sd_en_train (
    id SERIAL PRIMARY KEY,
    text_message TEXT  NOT NULL,
    label TEXT  NOT NULL
);

CREATE TABLE IF NOT EXISTS sd_en_test (
    id SERIAL PRIMARY KEY,
    text_message TEXT  NOT NULL,
    label TEXT  NOT NULL
);

CREATE TABLE IF NOT EXISTS sd_sp_train (
    id SERIAL PRIMARY KEY,
    text_message TEXT  NOT NULL,
    label TEXT  NOT NULL
);

CREATE TABLE IF NOT EXISTS sd_sp_test (
    id SERIAL PRIMARY KEY,
    text_message TEXT  NOT NULL,
    label TEXT  NOT NULL
);

CREATE TABLE IF NOT EXISTS sd_feed (
    id SERIAL PRIMARY KEY,
    text_message TEXT  NOT NULL,
    label TEXT  NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    rating REAL NOT NULL,
    text_message TEXT  NOT NULL
);