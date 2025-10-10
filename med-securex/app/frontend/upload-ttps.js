// scripts/upload-ttps.js
const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');

const serviceAccountPath = path.join(__dirname, 'serviceAccountKey.json'); // <-- place your key here
if (!fs.existsSync(serviceAccountPath)) {
  console.error('serviceAccountKey.json not found in scripts/. Place your Firebase service account JSON at scripts/serviceAccountKey.json');
  process.exit(1);
}

const serviceAccount = require(serviceAccountPath);

// JSON produced by: npx csvtojson src/components/dashboard/mitre_attack_dataset.csv > src/components/dashboard/mitre_attack_dataset.json
const jsonPath = path.join(__dirname, '..', 'src', 'components', 'dashboard', 'mitre_attack_dataset.json');
if (!fs.existsSync(jsonPath)) {
  console.error('Dataset not found at', jsonPath);
  process.exit(1);
}

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

const db = admin.firestore();

function sanitizeId(id) {
  if (!id) return null;
  // remove whitespace, slashes, and other illegal doc id characters; keep alnum, dash, underscore, dot
  return id.toString().trim().replace(/\s+/g, '_').replace(/[\/#\[\]\.\s]/g, '-');
}

function slugify(str) {
  return (str || '')
    .toString()
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

async function uploadAll() {
  const raw = fs.readFileSync(jsonPath, 'utf8');
  const rows = JSON.parse(raw);

  console.log(`🗂️  Loaded ${rows.length} rows from JSON`);

  const batchSize = 500; // Firestore batch limit
  let batch = db.batch();
  let counter = 0;
  let batchCount = 0;

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];

    // Prefer MITRE column for unique id
    let docId = sanitizeId(row.MITRE || row.Mitre || row.mitre);
    if (!docId) {
      // fallback to label/name or index
      docId = sanitizeId(row.Label || row.name || row.Name) || `ttp-${i}`;
    }

    // prepare payload - include commonly useful fields, but keep everything
    const payload = {
      // keep original keys (CSV headers) too so you can inspect them in Firestore
      ...row,
      mitre: row.MITRE || row.Mitre || row.mitre || null,
      name: row.Label || row.Label || row.name || row.Name || null,
      tactic: row.AttackType || row.Attack_Type || row.AttackType || null,
      severity: row.Severity || null,
      description: row.Description || row.description || null,
      lastSeen: new Date().toISOString()
    };

    const docRef = db.collection('mitreTechniques').doc(docId);
    batch.set(docRef, payload, { merge: true });
    counter++;

    if (counter >= batchSize) {
      batchCount++;
      console.log(`Committing batch #${batchCount} (written ${i + 1}/${rows.length})`);
      await batch.commit();
      batch = db.batch();
      counter = 0;
    }
  }

  if (counter > 0) {
    batchCount++;
    console.log(`Committing final batch #${batchCount}`);
    await batch.commit();
  }

  console.log('✅ Upload complete');
  process.exit(0);
}

uploadAll().catch(err => {
  console.error('Upload error:', err);
  process.exit(1);
});
