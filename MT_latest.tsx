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
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';

const ModelTraining = () => {
  const [envName, setEnvName] = useState('');
  const [envPurpose, setEnvPurpose] = useState('');
  const [useCase, setUseCase] = useState('');
  const [dataDomain, setDataDomain] = useState('');
  const [selectedIDE, setSelectedIDE] = useState('jupyter');
  const [computeSize, setComputeSize] = useState('small');
  const [containerImages, setContainerImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [jupyterLoading, setJupyterLoading] = useState(false);
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [createdRequestId, setCreatedRequestId] = useState<string | null>(null);
  const [jupyterDialogOpen, setJupyterDialogOpen] = useState(false);
  const [jupyterUrl, setJupyterUrl] = useState<string | null>(null);
  const [jupyterExpiry, setJupyterExpiry] = useState<string | null>(null);

  const handleContainerImageChange = (image: string) => {
    setContainerImages(prev =>
      prev.includes(image) ? prev.filter(item => item !== image) : [...prev, image]
    );
  };

  const handleCreate = async () => {
    if (!envName || !envPurpose) {
      setAlert({ type: 'error', message: 'Env Name and Env Purpose are required' });
      return;
    }
    setLoading(true);
    setAlert(null);

    const formData = {
      env_name: envName,
      env_purpose: envPurpose,
      use_case: useCase,
      data_domain: dataDomain,
      instance_type: computeSize,
      ide_option: selectedIDE,
      framework_option: containerImages.join(','),
      requested_by: 'anonymous',
      status: 'submitted',
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch('http://10.53.136.65:5000/env-request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(formData),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const result = await response.json();
      const requestId = result.request_id;
      setCreatedRequestId(requestId);
      setAlert({ type: 'success', message: `Environment Request Created! ID: ${requestId}` });

      if (selectedIDE === 'jupyter') {
        await handleJupyterAccess(requestId);
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        setAlert({ type: 'error', message: 'Request timeout – please check your connection' });
      } else {
        setAlert({ type: 'error', message: `Failed to create request: ${error.message}` });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleJupyterAccess = async (requestId: string) => {
    if (!requestId) {
      setAlert({ type: 'error', message: 'Request ID is missing' });
      return;
    }
    setJupyterLoading(true);
    setAlert(null);

    try {
      const url = `http://10.53.136.65:5000/generate-jupyter-url/${requestId}?expiry_minutes=30`;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const result = await response.json();
      if (result.success && result.data) {
        setJupyterUrl(result.data.presigned_url);
        setJupyterExpiry(new Date(result.data.expires_at).toLocaleString());
        setJupyterDialogOpen(true);
        setAlert({ type: 'success', message: 'Jupyter URL generated!' });
      } else {
        throw new Error('Invalid server response');
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        setAlert({ type: 'error', message: 'Timeout – please try again' });
      } else {
        setAlert({ type: 'error', message: `Failed to generate URL: ${error.message}` });
      }
    } finally {
      setJupyterLoading(false);
    }
  };

  const handleJupyterOpen = () => {
    if (jupyterUrl) {
      window.open(jupyterUrl, '_blank');
      setJupyterDialogOpen(false);
    }
  };

  const resetForm = () => {
    setEnvName('');
    setEnvPurpose('');
    setUseCase('');
    setDataDomain('');
    setSelectedIDE('jupyter');
    setComputeSize('small');
    setContainerImages([]);
    setAlert(null);
    setCreatedRequestId(null);
    setJupyterUrl(null);
    setJupyterExpiry(null);
  };

  return (
    <Container maxWidth="xl" sx={{ ml: '240px', display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Box my={4}>
        <Typography variant="h5"><b>Request for Environment</b></Typography>
      </Box>

      <Box mb={2}>
        <Button variant="contained" onClick={handleCreate} disabled={loading} sx={{ mr: 2 }}>
          {loading ? <CircularProgress size={24} /> : 'Create'}
        </Button>
        {createdRequestId && selectedIDE === 'jupyter' && (
          <Button
            variant="outlined"
            onClick={() => handleJupyterAccess(createdRequestId)}
            disabled={jupyterLoading}
            sx={{ mr: 2 }}
          >
            {jupyterLoading ? <CircularProgress size={20} /> : 'Generate Jupyter Access'}
          </Button>
        )}
        {createdRequestId && (
          <Button variant="outlined" onClick={resetForm}>
            New Request
          </Button>
        )}
      </Box>

      {alert && (
        <Alert severity={alert.type} onClose={() => setAlert(null)} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}

      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Env Name"
              fullWidth
              required
              value={envName}
              onChange={e => setEnvName(e.target.value)}
              disabled={loading}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Env Purpose"
              fullWidth
              required
              value={envPurpose}
              onChange={e => setEnvPurpose(e.target.value)}
              disabled={loading}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Use Case"
              fullWidth
              value={useCase}
              onChange={e => setUseCase(e.target.value)}
              disabled={loading}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Data Domain"
              fullWidth
              value={dataDomain}
              onChange={e => setDataDomain(e.target.value)}
              disabled={loading}
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={4}>
          <Grid item xs={12} sm={6} md={4}>
            <FormLabel>Compute</FormLabel>
            <RadioGroup value={computeSize} onChange={e => setComputeSize(e.target.value)}>
              {['small', 'medium', 'large'].map(size => (
                <FormControlLabel
                  key={size}
                  value={size}
                  control={<Radio />}
                  label={size}
                  disabled={loading}
                />
              ))}
            </RadioGroup>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormLabel>IDE</FormLabel>
            <RadioGroup value={selectedIDE} onChange={e => setSelectedIDE(e.target.value)}>
              {['jupyter', 'vscode', 'sas', 'studio'].map(ide => (
                <FormControlLabel
                  key={ide}
                  value={ide}
                  control={<Radio />}
                  label={ide === 'studio' ? 'Sagemaker Studio' : ide.charAt(0).toUpperCase() + ide.slice(1)}
                  disabled={loading}
                />
              ))}
            </RadioGroup>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormLabel>Container Images</FormLabel>
            <Box>
              {[
                { key: 'xgboost', label: 'XGBoost 1.7' },
                { key: 'tensorflow', label: 'TensorFlow 2.13' },
                { key: 'pytorch', label: 'PyTorch 2.1' },
                { key: 'custom', label: 'Custom Container' },
              ].map(img => (
                <FormControlLabel
                  key={img.key}
                  control={
                    <Checkbox
                      checked={containerImages.includes(img.key)}
                      onChange={() => handleContainerImageChange(img.key)}
                      disabled={loading}
                    />
                  }
                  label={img.label}
                />
              ))}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Dialog open={jupyterDialogOpen} onClose={() => setJupyterDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Jupyter Access Ready</DialogTitle>
        <DialogContent>
          <Typography paragraph>
            Your Jupyter environment is ready! Click below to access your secure session.
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Environment:</strong> {envName}
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Request ID:</strong> {createdRequestId}
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Valid until:</strong> {jupyterExpiry}
          </Typography>
          <Alert severity="info">
            This secure link expires in 30 minutes.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setJupyterDialogOpen(false)}>Close</Button>
          <Button variant="contained" onClick={handleJupyterOpen} disabled={!jupyterUrl}>
            Open Jupyter Lab
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ModelTraining;
