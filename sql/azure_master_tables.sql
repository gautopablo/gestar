-- Idempotent script for Azure SQL Query Editor
-- Creates master tables used by app_v2.

IF OBJECT_ID('master_catalogs','U') IS NULL
BEGIN
    CREATE TABLE master_catalogs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(100) NOT NULL,
        label NVARCHAR(255) NOT NULL,
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

IF OBJECT_ID('master_catalog_items','U') IS NULL
BEGIN
    CREATE TABLE master_catalog_items (
        id INT IDENTITY(1,1) PRIMARY KEY,
        catalog_id INT NOT NULL,
        code NVARCHAR(200) NULL,
        label NVARCHAR(255) NOT NULL,
        sort_order INT NOT NULL DEFAULT 0,
        is_active BIT NOT NULL DEFAULT 1,
        parent_item_id INT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_master_items_catalog
            FOREIGN KEY (catalog_id) REFERENCES master_catalogs(id),
        CONSTRAINT FK_master_items_parent
            FOREIGN KEY (parent_item_id) REFERENCES master_catalog_items(id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_master_catalogs_code'
      AND object_id = OBJECT_ID('master_catalogs')
)
BEGIN
    CREATE UNIQUE INDEX UX_master_catalogs_code ON master_catalogs(code);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_master_items_lookup'
      AND object_id = OBJECT_ID('master_catalog_items')
)
BEGIN
    CREATE INDEX IX_master_items_lookup
    ON master_catalog_items(catalog_id, is_active, sort_order, label);
END;
GO

-- Data seed is done by db.init_db() in app_v2.py.
-- Run app_v2 once after creating tables to populate current master values.
