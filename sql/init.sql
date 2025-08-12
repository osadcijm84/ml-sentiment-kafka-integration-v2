-- Create database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'SentimentDB')
BEGIN
    CREATE DATABASE SentimentDB;
END
GO

USE SentimentDB;
GO

-- Create table for storing sentiment predictions
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SentimentPredictions')
BEGIN
    CREATE TABLE SentimentPredictions (
        id INT IDENTITY(1,1) PRIMARY KEY,
        text NVARCHAR(MAX) NOT NULL,
        sentiment NVARCHAR(50) NOT NULL,
        confidence FLOAT NOT NULL,
        prediction_date DATETIME2 DEFAULT GETDATE(),
        model_version NVARCHAR(50) DEFAULT '1.0',
        created_at DATETIME2 DEFAULT GETDATE()
    );
END
GO

-- Create table for storing training/validation data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TrainingData')
BEGIN
    CREATE TABLE TrainingData (
        id INT IDENTITY(1,1) PRIMARY KEY,
        text NVARCHAR(MAX) NOT NULL,
        actual_sentiment NVARCHAR(50) NOT NULL,
        rating FLOAT,
        product_category NVARCHAR(100),
        data_source NVARCHAR(100) DEFAULT 'Amazon Reviews',
        created_at DATETIME2 DEFAULT GETDATE(),
        is_training BIT DEFAULT 1,
        is_validation BIT DEFAULT 0
    );
END
GO

-- Create table for model performance metrics
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ModelMetrics')
BEGIN
    CREATE TABLE ModelMetrics (
        id INT IDENTITY(1,1) PRIMARY KEY,
        model_version NVARCHAR(50) NOT NULL,
        accuracy FLOAT,
        precision_score FLOAT,
        recall_score FLOAT,
        f1_score FLOAT,
        training_date DATETIME2 DEFAULT GETDATE(),
        notes NVARCHAR(MAX)
    );
END
GO

-- Create indexes for better performance
CREATE NONCLUSTERED INDEX IX_SentimentPredictions_Date 
ON SentimentPredictions (prediction_date DESC);

CREATE NONCLUSTERED INDEX IX_TrainingData_Sentiment 
ON TrainingData (actual_sentiment);

CREATE NONCLUSTERED INDEX IX_ModelMetrics_Version 
ON ModelMetrics (model_version);
GO

-- Insert sample training data
INSERT INTO TrainingData (text, actual_sentiment, rating, product_category) VALUES
('This product is amazing! I love it so much.', 'positive', 5.0, 'Beauty'),
('Great quality and fast shipping. Highly recommended!', 'positive', 5.0, 'Beauty'),
('Perfect for my needs. Will buy again.', 'positive', 4.0, 'Beauty'),
('Terrible product. Waste of money.', 'negative', 1.0, 'Beauty'),
('Poor quality and arrived damaged.', 'negative', 1.0, 'Beauty'),
('Not what I expected. Very disappointed.', 'negative', 2.0, 'Beauty'),
('Good product but could be better.', 'positive', 3.0, 'Beauty'),
('Average quality for the price.', 'positive', 3.0, 'Beauty');
GO

-- Insert initial model metrics
INSERT INTO ModelMetrics (model_version, accuracy, precision_score, recall_score, f1_score, notes) VALUES
('1.0', 0.9304, 0.93, 0.93, 0.93, 'Initial model trained on Amazon Beauty reviews dataset');
GO

PRINT 'Database initialization completed successfully!';

