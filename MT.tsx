import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  FormControlLabel,
  RadioGroup,
  Radio,
  FormLabel,
  Checkbox,
  Grid,
  Paper,
} from '@mui/material';

const ModelTraining = () => {
  const [envName, setEnvName] = useState('');
  const [envPurpose, setEnvPurpose] = useState('');
  const [useCase, setUseCase] = useState('');
  const [dataDomain, setDataDomain] = useState('');
  const [selectedIDE, setSelectedIDE] = useState('jupyter');
  const [computeSize, setComputeSize] = useState('small');
  const [containerImages, setContainerImages] = useState<string[]>([]);

  const handleContainerImageChange = (image: string) => {
    setContainerImages((prev) =>
      prev.includes(image)
        ? prev.filter((item) => item !== image)
        : [...prev, image]
    );
  };

  const handleCreate = async () => {
    if (!envName || !envPurpose) {
      alert('Env Name and Env Purpose are required');
      return;
    }

    const formData = {
      env_name: envName,
      env_purpose: envPurpose,
      use_case: useCase,
      data_domain: dataDomain,
      instance_type: computeSize,
      ide_option: selectedIDE,
      framework_option: containerImages.join(','), // send as comma-separated string
    };

    try {
      const response = await fetch('http://localhost:8000/env-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`API responded with status ${response.status}`);
      }

      const result = await response.json();
      alert(`Environment Request Created. Request ID: ${result.request_id}`);

      if (selectedIDE === 'jupyter') {
        window.open('http://10.53.136.65:8888/', '_blank');
      }
    } catch (error) {
      console.error('API Error:', error);
      alert('Failed to send environment request');
    }
  };

  return (
    <Container maxWidth="xl" style={{ marginLeft: '240px', display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" my={4}>
        <Typography variant="h5">
          <b>Request for Environment</b>
        </Typography>
        <Button variant="contained" color="primary" onClick={handleCreate}>
          Create
        </Button>
      </Box>

      {/* Section 1: Basic Environment Info */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <TextField label="Env Name" fullWidth required value={envName} onChange={(e) => setEnvName(e.target.value)} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField label="Env Purpose" fullWidth required value={envPurpose} onChange={(e) => setEnvPurpose(e.target.value)} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField label="Use Case" fullWidth value={useCase} onChange={(e) => setUseCase(e.target.value)} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField label="Data Domain" fullWidth value={dataDomain} onChange={(e) => setDataDomain(e.target.value)} />
          </Grid>
        </Grid>
      </Paper>

      {/* Section 2: Data Products */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6">Structured Data Products</Typography>
        <Button variant="outlined" sx={{ my: 1 }}>Browse Metadata Catalog</Button>
        <Typography>Snowflake: DB1 T1, T8 & T10</Typography>
        <Typography>AWS Glue: DB2 T20 & T30</Typography>

        <Typography variant="h6" sx={{ mt: 4 }}>Unstructured Data Products</Typography>
        <Typography>s3://bucket-1/folder-1</Typography>
        <Typography>gfs://bucket-2/folder-2</Typography>
      </Paper>

      {/* Section 3: Compute / IDE / Collaboration */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={4}>
          <Grid item xs={12} sm={6} md={4}>
            <FormLabel>Compute</FormLabel>
            <RadioGroup value={computeSize} onChange={(e) => setComputeSize(e.target.value)}>
              <FormControlLabel value="small" control={<Radio />} label="Small" />
              <FormControlLabel value="medium" control={<Radio />} label="Medium" />
              <FormControlLabel value="large" control={<Radio />} label="Large" />
            </RadioGroup>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <FormLabel>IDE</FormLabel>
            <RadioGroup value={selectedIDE} onChange={(e) => setSelectedIDE(e.target.value)}>
              <FormControlLabel value="jupyter" control={<Radio />} label="Jupyter Notebook" />
              <FormControlLabel value="vscode" control={<Radio />} label="VSCode" />
              <FormControlLabel value="sas" control={<Radio />} label="SAS Studio" />
              <FormControlLabel value="studio" control={<Radio />} label="Sagemaker Studio" />
            </RadioGroup>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <FormLabel>Container Images</FormLabel>
            <Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={containerImages.includes('xgboost')}
                    onChange={() => handleContainerImageChange('xgboost')}
                  />
                }
                label="XGBoost 1.7"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={containerImages.includes('tensorflow')}
                    onChange={() => handleContainerImageChange('tensorflow')}
                  />
                }
                label="TensorFlow 2.13"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={containerImages.includes('pytorch')}
                    onChange={() => handleContainerImageChange('pytorch')}
                  />
                }
                label="PyTorch 2.1"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={containerImages.includes('custom')}
                    onChange={() => handleContainerImageChange('custom')}
                  />
                }
                label="Custom Container"
              />
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default ModelTraining;
