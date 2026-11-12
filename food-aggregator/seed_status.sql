-- order_statuses catalog + EXAMPLE vendor mappings. Rows marked TBD must be confirmed against vendor docs.
SET search_path TO "order";

INSERT INTO order_statuses (code, rank, is_terminal, is_active, description) VALUES
  ('RECEIVED',           10, false, true,  'Order accepted into OMS'),
  ('PENDING_PAYMENT',    15, false, false, 'RESERVED: own-channel prepaid, waiting authorize/capture'),
  ('CONFIRMED',          30, false, true,  'POS accepted / ticket confirmed'),
  ('PREPARING',          40, false, true,  'Kitchen cooking'),
  ('READY',              50, false, true,  'Ready for pickup / rider'),
  ('OUT_FOR_DELIVERY',   60, false, true,  'Rider picked up / en route (delivery only)'),
  ('DELIVERED',          70, false, true,  'Handed to customer (delivery); pickup usually skips to COMPLETED'),
  ('AWAITING_PAYMENT',   75, false, false, 'RESERVED: postpaid session bill unpaid'),
  ('COMPLETED',         100, true,  true,  'Done'),
  ('CANCELLED',         100, true,  true,  'Cancelled'),
  ('REJECTED',          100, true,  true,  'POS / channel rejected'),
  ('FAILED',            100, true,  true,  'Hard failure after retries');

-- EXAMPLES. Grab values from Grab public FoodPartner API (OrderStateRequest.state). Confirm against your integration.
-- DRIVER_ALLOCATED / DRIVER_ARRIVED: logged in history + Mongo, do not advance status (kitchen may still be cooking).
-- Grab DELIVERED -> DELIVERED; for PICKUP, rollup elevates to COMPLETED.
INSERT INTO status_mappings (source, raw_status, status_code, note) VALUES
  ('GRAB', 'COLLECTED',  'OUT_FOR_DELIVERY', 'example, Grab docs — picked up; apply only if current >= READY'),
  ('GRAB', 'DELIVERED',  'DELIVERED',        'example, Grab docs; pickup: rollup elevates to COMPLETED'),
  ('GRAB', 'FAILED',     'FAILED',           'example, Grab docs'),
  ('GRAB', 'CANCELLED',  'CANCELLED',        'example; Grab cancel is final for the order'),
  ('LINEMAN', 'TBD_PICKED_UP', 'OUT_FOR_DELIVERY', 'TBD: LINE MAN code unknown'),
  ('LINEMAN', 'TBD_DELIVERED', 'DELIVERED',        'TBD'),
  ('LINEMAN', 'TBD_CANCELLED', 'CANCELLED',        'TBD'),
  ('BSL', 'TBD_ACCEPTED', 'CONFIRMED', 'TBD: BSL webhook code unknown'),
  ('BSL', 'TBD_COOKING',  'PREPARING', 'TBD'),
  ('BSL', 'TBD_READY',    'READY',     'TBD'),
  ('BSL', 'TBD_VOID',     'CANCELLED', 'TBD'),
  ('SDM', 'UpdateOrder:OK', 'CONFIRMED', 'example: SDM UpdateOrder success = ticket created'),
  ('SDM', 'TBD_STATUS',     'CONFIRMED', 'TBD: SDM status codes / polling unknown'),
  ('OWN_FLEET', 'TBD_picked_up', 'OUT_FOR_DELIVERY', 'future, TBD'),
  ('PAYMENT',   'TBD_successful','CONFIRMED',        'RESERVED future: own-channel payment success leaves PENDING_PAYMENT');
