// Create the read-only Mongo user the AI assistant will use.
// Run as a user with userAdmin on the app DB.
//
// Why this user exists: the assistant's permission floor. Even if every
// in-IDE rule and hook fails, the server itself refuses writes.

use("app");

db.createUser({
  user: "ai_local",
  pwd: passwordPrompt(),
  roles: [
    { role: "read", db: "app" }
  ]
});

// Sanity: no write role, no dbAdmin, no clusterMonitor.
print("Created ai_local. Roles:");
printjson(db.getUser("ai_local").roles);
