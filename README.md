# DBeditor

[![.github/workflows/test.yaml](https://github.com/BazaroZero/DBeditor/actions/workflows/test.yaml/badge.svg?branch=master)](https://github.com/BazaroZero/DBeditor/actions/workflows/test.yaml)
[![codecov](https://codecov.io/gh/BazaroZero/DBeditor/branch/master/graph/badge.svg?token=TYR87DHTP4)](https://codecov.io/gh/BazaroZero/DBeditor)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Easy to use** SQL databases editor with **minimalistic** design

## Install

```sh
git clone https://github.com/BazaroZero/DBeditor.git
pip install -r requirements.txt
```

## Usage

```sh
python dbeditor.py
```

## Features
- Menu file:
    - Open database (SQLite), create database (SQLite) and connect to remote database (MySQL or PostgreSQL)
    - Import data from csv and excel
    - Save added tables and inserted rows
- Menu structure:
    - Add new table
    - Add new columns (currently not allowed to add columns to existing tables)
    - Drop table
- Menu Settings:
    - You can choose how to find row in your table: by rowid or by primary keys (this affects editing and deleting values)
- Menu tables:
    - After opening the database, the menu will list your tables
- Right-click context menu:
    - Insert row
    - Open custom query window (It's unable to query unsaved table)
    - Delete row 