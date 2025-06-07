import React, { useState } from 'react';
import axios from 'axios';
import { log } from './logger';


const masterData = [
  'Coca-Cola Can',
  'Sprite Bottle',
  'Fanta Bottle',
];

function App() {
  const [file, setFile] = useState(null);
  const [products, setProducts] = useState([]);
  const [labels, setLabels] = useState({});

  const handleUpload = async () => {
    if (!file) return;

    log('Uploading image');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post('/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      log(`Received ${res.data.products.length} products`);
      setProducts(res.data.products);
    } catch (err) {
      log(`Upload failed: ${err}`);
    }
  };

  const handleChange = (clusterId, value) => {
    setLabels(prev => ({ ...prev, [clusterId]: value }));
  };

  const handleSubmit = async () => {

    log('Saving labels');
    try {
      await axios.post('/save-labels', labels);
      alert('Labels saved');
    } catch (err) {
      log(`Save failed: ${err}`);
    }

  };

  return (
    <div className="p-4">
      <input type="file" onChange={e => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Upload</button>
      <div className="mt-4">
        {products.map((p, idx) => (
          <div key={idx} className="mb-4 border p-2">
            <img src={`data:image/jpeg;base64,${p.image}`} width={100} />
            <select onChange={e => handleChange(p.cluster_id, e.target.value)}>
              <option value="">Select label</option>
              {masterData.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Custom label"
              onBlur={e => handleChange(p.cluster_id, e.target.value)}
            />
          </div>
        ))}
      </div>
      {products.length > 0 && (
        <button onClick={handleSubmit}>Save Labels</button>
      )}
    </div>
  );
}

export default App;
