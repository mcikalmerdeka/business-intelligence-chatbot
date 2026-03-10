# Olist Brazilian E-Commerce Database Documentation

## Database Overview

The Olist dataset is a public Brazilian e-commerce dataset containing orders placed on the Olist marketplace between 2016 and 2018. It covers the full order lifecycle from purchase to delivery and customer review, with information on customers, sellers, products, payments, and logistics.

**Schema Name:** `olist`
**Total Tables:** 8
**Key Relationships:** orders is the central table, linked to customers, order_items, order_payments, order_reviews. order_items links to products and sellers. geolocation provides zip-code-level coordinates for customers and sellers.

---

## Important Notes

**customer_unique_id vs customer_id:**
- `olist.customers.customer_id` — one row per order (used to join with `olist.orders`)
- `olist.customers.customer_unique_id` — identifies the same physical customer across multiple orders
- `olist.orders` does **NOT** have a `customer_unique_id` column. To count unique customers, join `orders → customers` and use `customers.customer_unique_id`.

---

## Table Descriptions

### 1. customers

Stores customer information. Each row is a unique order-customer pair; use `customer_unique_id` to identify the same person across orders.

**Table Name:** `olist.customers`
**Primary Key:** `customer_id`

#### Columns:
| Column Name | Data Type | Description |
|---|---|---|
| customer_id | VARCHAR(255) | Primary key. Unique ID per order (links to olist.orders.customer_id) |
| customer_unique_id | VARCHAR(255) | Identifies the same customer across multiple orders |
| customer_zip_code_prefix | VARCHAR(255) | First 5 digits of customer zip code |
| customer_city | VARCHAR(255) | Customer city name |
| customer_state | VARCHAR(255) | Two-letter Brazilian state code |

#### Relationships:
- Referenced by `olist.orders.customer_id` (One-to-Many)
- Joinable to `olist.geolocation` via `customer_zip_code_prefix = geolocation_zip_code_prefix`

---

### 2. geolocation

Maps Brazilian zip code prefixes to geographic coordinates.

**Table Name:** `olist.geolocation`

#### Columns:
| Column Name | Data Type | Description |
|---|---|---|
| geolocation_zip_code_prefix | VARCHAR(255) | 5-digit zip code prefix |
| geolocation_lat | FLOAT | Latitude |
| geolocation_lng | FLOAT | Longitude |
| geolocation_city | VARCHAR(255) | City name |
| geolocation_state | VARCHAR(255) | Two-letter state code |

#### Relationships:
- Joinable to `olist.customers` and `olist.sellers` via zip code prefix

---

### 3. order_items

Line items within each order. One order can have multiple items from different sellers.

**Table Name:** `olist.order_items`

#### Columns:
| Column Name | Data Type | Description |
|---|---|---|
| order_id | VARCHAR(255) | Links to olist.orders.order_id |
| order_item_id | INT | Sequential item number within the order (1, 2, 3 …) |
| product_id | VARCHAR(255) | Links to olist.products.product_id |
| seller_id | VARCHAR(255) | Links to olist.sellers.seller_id |
| shipping_limit_date | TIMESTAMP | Deadline for seller to hand off to carrier |
| price | FLOAT | Item price in BRL |
| freight_value | FLOAT | Freight cost for this item in BRL |

#### Relationships:
- References `olist.orders`, `olist.products`, `olist.sellers`

---

### 4. order_payments

Payment details for each order. One order may have multiple payment entries (e.g. voucher + credit card).

**Table Name:** `olist.order_payments`

#### Columns:
| Column Name | Data Type | Description |
|---|---|---|
| order_id | VARCHAR(255) | Links to olist.orders.order_id |
| payment_sequential | INT | Sequence number when multiple payment methods are used |
| payment_type | VARCHAR(255) | Payment method: credit_card, boleto, voucher, debit_card |
| payment_installments | INT | Number of installments chosen by the customer |
| payment_value | FLOAT | Transaction value in BRL |

#### Relationships:
- References `olist.orders.order_id`

---

### 5. order_reviews

Customer reviews left after delivery. One review per order.

**Table Name:** `olist.order_reviews`

#### Columns:
| Column Name | Data Type | Description |
|---|---|---|
| review_id | VARCHAR(255) | Unique review identifier |
| order_id | VARCHAR(255) | Links to olist.orders.order_id |
| review_score | INT | Rating from 1 (worst) to 5 (best) |
| review_comment_title | VARCHAR(255) | Optional review title |
| review_comment_message | VARCHAR(255) | Optional review body text |
| review_creation_date | TIMESTAMP | Date the review form was sent to the customer |
| review_answer_timestamp | TIMESTAMP | Date and time the customer submitted the review |

#### Relationships:
- References `olist.orders.order_id`

---

### 6. orders

Central table. Each row is one order and tracks its full lifecycle.

**Table Name:** `olist.orders`
**Primary Key:** `order_id`

#### Columns:
| Column Name | Data Type | Description |
|---|---|---|
| order_id | VARCHAR(255) | Primary key. Unique order identifier |
| customer_id | VARCHAR(255) | Links to olist.customers.customer_id |
| order_status | VARCHAR(255) | Status: delivered, shipped, canceled, invoiced, processing, approved, unavailable, created |
| order_purchase_timestamp | TIMESTAMP | Timestamp when the customer placed the order |
| order_approved_at | TIMESTAMP | Timestamp when payment was approved |
| order_delivered_carrier_date | TIMESTAMP | Timestamp when order was handed to the carrier |
| order_delivered_customer_date | TIMESTAMP | Timestamp when order was delivered to the customer |
| order_estimated_delivery_date | TIMESTAMP | Estimated delivery date shown to customer at purchase |

#### Relationships:
- References `olist.customers`
- Referenced by `olist.order_items`, `olist.order_payments`, `olist.order_reviews`

---

### 7. products

Product catalog with physical dimensions.

**Table Name:** `olist.products`

#### Columns:
| Column Name | Data Type | Description |
|---|---|---|
| product_id | VARCHAR(255) | Unique product identifier |
| product_category_name | VARCHAR(255) | Product category (in Portuguese) |
| product_name_lenght | INT | Number of characters in product name |
| product_description_lenght | INT | Number of characters in product description |
| product_photos_qty | INT | Number of product photos published |
| product_weight_g | INT | Product weight in grams |
| product_length_cm | INT | Product length in centimeters |
| product_height_cm | INT | Product height in centimeters |
| product_width_cm | INT | Product width in centimeters |

#### Relationships:
- Referenced by `olist.order_items.product_id`

---

### 8. sellers

Seller information.

**Table Name:** `olist.sellers`
**Primary Key:** `seller_id`

#### Columns:
| Column Name | Data Type | Description |
|---|---|---|
| seller_id | VARCHAR(255) | Unique seller identifier |
| seller_zip_code_prefix | VARCHAR(255) | First 5 digits of seller zip code |
| seller_city | VARCHAR(255) | Seller city |
| seller_state | VARCHAR(255) | Two-letter state code |

#### Relationships:
- Referenced by `olist.order_items.seller_id`
- Joinable to `olist.geolocation` via `seller_zip_code_prefix`

---

## Key Relationships Summary

```
olist.customers ──< olist.orders ──< olist.order_items >── olist.products
                         │
                         ├──< olist.order_payments
                         └──< olist.order_reviews

olist.order_items >── olist.sellers

olist.customers  >── olist.geolocation  (via zip_code_prefix)
olist.sellers    >── olist.geolocation  (via zip_code_prefix)
```

## Common Query Patterns

- **Revenue analysis**: JOIN orders + order_items + order_payments, GROUP BY time/category/state
- **Delivery performance**: orders table, compare order_delivered_customer_date vs order_estimated_delivery_date
- **Customer satisfaction**: JOIN orders + order_reviews, GROUP BY review_score
- **Seller performance**: JOIN order_items + sellers + orders, aggregate price/freight
- **Product categories**: JOIN order_items + products, GROUP BY product_category_name
