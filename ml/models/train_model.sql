-- BigQuery ML Anomaly Detection Model
-- This SQL creates and trains a logistic regression model to predict anomalies

-- Step 1: Create and train the model
CREATE OR REPLACE MODEL `PROJECT_ID.osprey_data.anomaly_predictor_v1`
OPTIONS(
  model_type='LOGISTIC_REG',
  input_label_cols=['is_test_data'],
  data_split_method='AUTO_SPLIT',
  data_split_eval_fraction=0.3,
  max_iterations=20,
  learn_rate_strategy='line_search',
  early_stop=TRUE,
  min_rel_progress=0.01
) AS
SELECT 
  sentiment_score,
  title_length,
  content_length,
  num_stocks,
  age_hours,
  published_hour,
  is_test_data
FROM `PROJECT_ID.osprey_data.training_data`
WHERE is_test_data IS NOT NULL;

-- Step 2: Evaluate the model
SELECT *
FROM ML.EVALUATE(
  MODEL `PROJECT_ID.osprey_data.anomaly_predictor_v1`
);

-- Step 3: Get feature importance
SELECT *
FROM ML.FEATURE_IMPORTANCE(
  MODEL `PROJECT_ID.osprey_data.anomaly_predictor_v1`
);

-- Step 4: Make predictions on new data (last 7 days)
CREATE OR REPLACE TABLE `PROJECT_ID.osprey_data.ml_predictions` AS
SELECT
  article_id,
  predicted_is_test_data,
  predicted_is_test_data_probs[OFFSET(1)].prob as anomaly_probability,
  title,
  author,
  published_at
FROM ML.PREDICT(
  MODEL `PROJECT_ID.osprey_data.anomaly_predictor_v1`,
  (
    SELECT
      article_id,
      sentiment_score,
      LENGTH(title) as title_length,
      LENGTH(content) as content_length,
      ARRAY_LENGTH(SPLIT(stock_symbols, ',')) as num_stocks,
      TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), published_at, HOUR) as age_hours,
      EXTRACT(HOUR FROM published_at) as published_hour,
      title,
      author,
      published_at
    FROM `PROJECT_ID.osprey_data.raw_news`
    WHERE published_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  )
)
WHERE predicted_is_test_data = TRUE
ORDER BY anomaly_probability DESC;

-- Step 5: Get high-confidence predictions
SELECT
  article_id,
  anomaly_probability,
  title,
  author,
  published_at
FROM `PROJECT_ID.osprey_data.ml_predictions`
WHERE anomaly_probability > 0.70
ORDER BY anomaly_probability DESC
LIMIT 50;
