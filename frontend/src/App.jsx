import React, { useState, useEffect } from 'react';
import axios from 'axios';
axios.defaults.baseURL = 'http://localhost:8000';
import { log } from './logger';

const initialLabels = [
  'Coca-Cola Can',
  'Sprite Bottle',
  'Fanta Bottle',
];

const colors = [
  '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
  '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabebe',
];

function BoxOverlay({ image, detections, width, height, colorMap, defaultColors = [], unlabeledColor = '#808080' }) {
  const [dims, setDims] = useState({ w: 1, h: 1 });
  const imgRef = React.useRef(null);

  useEffect(() => {
    const updateDims = () => {
      if (imgRef.current) {
        setDims({ w: imgRef.current.clientWidth, h: imgRef.current.clientHeight });
      }
    };
    updateDims();
    window.addEventListener('resize', updateDims);
    return () => window.removeEventListener('resize', updateDims);
  }, [image]);
  const scale = (val, max, disp) => (val / max) * disp;
  return (
    <div style={{ position: 'relative', display: 'inline-block', maxWidth: '600px', width: '100%' }}>
      <img
        src={`data:image/jpeg;base64,${image}`}
        ref={imgRef}
        alt="shelf"
        style={{ maxWidth: '100%', height: 'auto', display: 'block' }}
      />
      {detections.map((d, idx) => {
        const [x1, y1, x2, y2] = d.bbox;
        let color = colorMap[d.cluster_id];
        if (!color) {
          if (defaultColors.length) {
            color = defaultColors[d.cluster_id % defaultColors.length];
          } else {
            color = unlabeledColor;
          }
        }
        const left = scale(x1, width, dims.w);
        const top = scale(y1, height, dims.h);
        const boxW = scale(x2 - x1, width, dims.w);
        const boxH = scale(y2 - y1, height, dims.h);
        return (
          <div
            key={idx}
            style={{
              position: 'absolute',
              left,
              top,
              width: boxW,
              height: boxH,
              border: `2px solid ${color}`,
              boxSizing: 'border-box',
            }}
          />
        );
      })}
    </div>
  );
}

function ShareChart({ counts }) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  return (
    <div>
      {Object.entries(counts).map(([label, count]) => {
        const pct = total ? (count / total) * 100 : 0;
        return (
          <div key={label} style={{ margin: '4px 0' }}>
            <div style={{ fontSize: '0.9em' }}>{label} - {pct.toFixed(1)}%</div>
            <div style={{ background: '#ddd', height: '10px', position: 'relative' }}>
              <div style={{ width: `${pct}%`, background: '#69c', height: '10px' }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function App() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [image, setImage] = useState(null);
  const [detections, setDetections] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [imgWidth, setImgWidth] = useState(1);
  const [imgHeight, setImgHeight] = useState(1);
  const [clusterCount, setClusterCount] = useState(10);
  const [labels, setLabels] = useState({});
  const [defaultLabels, setDefaultLabels] = useState({});
  const [labelOptions, setLabelOptions] = useState(initialLabels);
  const [newLabel, setNewLabel] = useState('');
  const [loading, setLoading] = useState(false);

  const uploadAndCluster = async (n) => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      setLoading(true);
      const res = await axios.post(`/upload-image?clusters=${n}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setImage(res.data.image);
      setImgWidth(res.data.width);
      setImgHeight(res.data.height);
      setDetections(res.data.detections);
      setClusters(res.data.clusters);
      const defaults = {};
      res.data.clusters.forEach(c => {
        if (defaultLabels[c.cluster_id]) {
          defaults[c.cluster_id] = defaultLabels[c.cluster_id];
        }
      });
      setLabels(defaults);
    } catch (err) {
      log('upload failed ' + err);
    } finally {
      setLoading(false);
    }
  };

  const handleNext1 = () => {
    if (!file) return;
    setStep(2);
    setLoading(true);
    uploadAndCluster(clusterCount);
  };

  const handleClusterSlider = (e) => {
    const n = parseInt(e.target.value, 10);
    setClusterCount(n);
    uploadAndCluster(n);
  };

  const addLabel = () => {
    if (newLabel && !labelOptions.includes(newLabel)) {
      setLabelOptions([...labelOptions, newLabel]);
      setNewLabel('');
    }
  };

  const handleLabel = (cid, value) => {
    setLabels(prev => ({ ...prev, [cid]: value }));
    if (value && !labelOptions.includes(value)) {
      setLabelOptions([...labelOptions, value]);
    }
  };

  const handleSave = async () => {
    await axios.post('/save-labels', labels);
    setStep(3);
  };

  const handleStartOver = () => {
    setFile(null);
    setImage(null);
    setDetections([]);
    setClusters([]);
    setLabels({});
    setDefaultLabels({});
    setStep(1);
  };

  const handleApplyNewShelf = () => {
    setDefaultLabels(labels);
    setFile(null);
    setImage(null);
    setDetections([]);
    setClusters([]);
    setLabels({});
    setStep(1);
  };

  const shareCounts = () => {
    const counts = {};
    detections.forEach(d => {
      const label = labels[d.cluster_id];
      if (!label) return;
      counts[label] = (counts[label] || 0) + 1;
    });
    return counts;
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <div style={{ marginBottom: '20px', fontWeight: 'bold' }}>
        {[1,2,3].map(n => (
          <span key={n} style={{ color: step === n ? '#007bff' : '#000' }}>
            {n}
            {n < 3 && ' > '}
          </span>
        ))}
      </div>

      {step === 1 && (
        <div>
          <input type="file" onChange={e => setFile(e.target.files[0])} />
          <div style={{ marginTop: '20px' }}>
            <button onClick={handleNext1}>Next</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div>
          {loading && <div>Loading...</div>}
          {image && (
            <div>
              <BoxOverlay
                image={image}
                detections={detections}
                width={imgWidth}
                height={imgHeight}
                colorMap={{}}
                defaultColors={colors}
              />
            </div>
          )}
          <div style={{ margin: '20px 0' }}>
            Clusters: {clusterCount}
            <input type="range" min="2" max="20" value={clusterCount} onChange={handleClusterSlider} />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <input
              type="text"
              placeholder="Add label"
              value={newLabel}
              onChange={e => setNewLabel(e.target.value)}
            />
            <button type="button" onClick={addLabel}>Add</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap' }}>
            {clusters.map(c => (
              <div key={c.cluster_id} style={{ margin: '10px', textAlign: 'center' }}>
                <img src={`data:image/jpeg;base64,${c.image}`} width={80} />
                <input
                  type="text"
                  list="label-options"
                  value={labels[c.cluster_id] || ''}
                  onChange={e => handleLabel(c.cluster_id, e.target.value)}
                  style={{ width: '100px' }}
                />
              </div>
            ))}
            <datalist id="label-options">
              {labelOptions.map(m => (
                <option key={m} value={m} />
              ))}
            </datalist>
          </div>
          <button onClick={handleSave}>Save Labels</button>
        </div>
      )}

      {step === 3 && (
        <div>
          {image && (
            <BoxOverlay
              image={image}
              detections={detections}
              width={imgWidth}
              height={imgHeight}
              colorMap={(function () {
                const labelColors = {};
                Object.values(labels).forEach((lab, i) => {
                  if (!labelColors[lab]) {
                    labelColors[lab] = colors[i % colors.length];
                  }
                });
                const map = {};
                Object.entries(labels).forEach(([cid, lab]) => {
                  map[cid] = labelColors[lab];
                });
                return map;
              })()}
              unlabeledColor="#808080"
            />
          )}
          <h3>Share of facings</h3>
          <ShareChart counts={shareCounts()} />
          <div style={{ marginTop: '20px' }}>
            <button onClick={handleStartOver} style={{ marginRight: '10px' }}>Start Over</button>
            <button onClick={handleApplyNewShelf}>New Shelf</button>
          </div>
        </div>
      )}
    </div>
  );
}
