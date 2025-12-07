db = db.getSiblingDB("ledger");

db.createUser({
  user: "ledger",
  pwd: "password",
  roles: [{ role: "readWrite", db: "ledger" }],
});
