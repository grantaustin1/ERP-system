import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Upload, FileText, CheckCircle, AlertCircle, Download, History, Users, UserPlus, ArrowRight, Shield } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function DataImport() {
  const [activeTab, setActiveTab] = useState('import');
  const [importType, setImportType] = useState('members');
  const [step, setStep] = useState(1); // 1: Upload, 2: Mapping, 3: Review, 4: Complete
  
  // Upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [parsedData, setParsedData] = useState(null);
  
  // Mapping state
  const [fieldDefinitions, setFieldDefinitions] = useState([]);
  const [fieldMapping, setFieldMapping] = useState({});
  
  // Duplicate handling
  const [duplicateAction, setDuplicateAction] = useState('skip'); // skip, update, create
  
  // Import state
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  
  // History state
  const [importLogs, setImportLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchImportLogs();
    }
  }, [activeTab]);

  useEffect(() => {
    if (step === 2) {
      fetchFieldDefinitions();
    }
  }, [step, importType]);

  const fetchFieldDefinitions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/import/field-definitions?import_type=${importType}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setFieldDefinitions(data.fields);
        
        // Initialize empty mapping
        const initialMapping = {};
        data.fields.forEach(field => {
          initialMapping[field.key] = '';
        });
        setFieldMapping(initialMapping);
      }
    } catch (error) {
      console.error('Failed to fetch field definitions:', error);
    }
  };

  const fetchImportLogs = async () => {
    setLoadingLogs(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/import/logs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setImportLogs(data);
      }
    } catch (error) {
      console.error('Failed to fetch import logs:', error);
    } finally {
      setLoadingLogs(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${BACKEND_URL}/api/import/parse-csv`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setParsedData(data);
        setStep(2);
      } else {
        const error = await response.json();
        alert(`Failed to parse file: ${error.detail}`);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleAutoMap = () => {
    if (!parsedData) return;
    
    const newMapping = { ...fieldMapping };
    
    // Try to auto-match columns
    parsedData.headers.forEach(csvHeader => {
      const lowerHeader = csvHeader.toLowerCase().replace(/[_\s]/g, '');
      
      fieldDefinitions.forEach(field => {
        const lowerField = field.key.toLowerCase().replace(/[_\s]/g, '');
        
        // Check for exact or partial matches
        if (lowerHeader === lowerField || 
            lowerHeader.includes(lowerField) || 
            lowerField.includes(lowerHeader)) {
          newMapping[field.key] = csvHeader;
        }
      });
    });
    
    setFieldMapping(newMapping);
  };

  const handleImport = async () => {
    setImporting(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('field_mapping', JSON.stringify(fieldMapping));
      formData.append('duplicate_action', duplicateAction);

      const endpoint = importType === 'members' ? '/api/import/members' : '/api/import/leads';
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setImportResult(result);
        setStep(4);
      } else {
        const error = await response.json();
        alert(`Import failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Import failed:', error);
      alert('Import failed');
    } finally {
      setImporting(false);
    }
  };

  const resetImport = () => {
    setStep(1);
    setSelectedFile(null);
    setParsedData(null);
    setFieldMapping({});
    setImportResult(null);
  };

  const getMappedCount = () => {
    return Object.values(fieldMapping).filter(val => val !== '' && val !== '__NONE__').length;
  };

  const getRequiredMapped = () => {
    const required = fieldDefinitions.filter(f => f.required);
    const mappedRequired = required.filter(f => fieldMapping[f.key] !== '' && fieldMapping[f.key] !== '__NONE__');
    return mappedRequired.length === required.length;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Data Import</h1>
        <p className="text-gray-600 mt-1">Import member databases and lead lists with field mapping</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="import">Import Data</TabsTrigger>
          <TabsTrigger value="history">Import History</TabsTrigger>
        </TabsList>

        <TabsContent value="import" className="space-y-6">
          {/* Progress Steps */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className={`flex items-center space-x-2 ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>1</div>
                  <span className="font-medium">Upload File</span>
                </div>
                <ArrowRight className="text-gray-400" />
                <div className={`flex items-center space-x-2 ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>2</div>
                  <span className="font-medium">Map Fields</span>
                </div>
                <ArrowRight className="text-gray-400" />
                <div className={`flex items-center space-x-2 ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>3</div>
                  <span className="font-medium">Review & Import</span>
                </div>
                <ArrowRight className="text-gray-400" />
                <div className={`flex items-center space-x-2 ${step >= 4 ? 'text-green-600' : 'text-gray-400'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 4 ? 'bg-green-600 text-white' : 'bg-gray-200'}`}>4</div>
                  <span className="font-medium">Complete</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Step 1: Upload */}
          {step === 1 && (
            <Card>
              <CardHeader>
                <CardTitle>Step 1: Upload CSV File</CardTitle>
                <CardDescription>Select the type of data and upload your CSV file</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Import Type</Label>
                  <Select value={importType} onValueChange={setImportType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="members">
                        <div className="flex items-center space-x-2">
                          <Users className="h-4 w-4" />
                          <span>Members (Acquired Gym Database)</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="leads">
                        <div className="flex items-center space-x-2">
                          <UserPlus className="h-4 w-4" />
                          <span>Leads (Prospect Lists)</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Button variant="outline" onClick={() => document.getElementById('file-upload').click()}>
                      Choose CSV File
                    </Button>
                  </label>
                  {selectedFile && (
                    <div className="mt-4">
                      <div className="flex items-center justify-center space-x-2 text-sm">
                        <FileText className="h-4 w-4" />
                        <span>{selectedFile.name}</span>
                      </div>
                    </div>
                  )}
                  <p className="text-sm text-gray-500 mt-2">Upload a CSV file with your data</p>
                </div>

                <Button
                  onClick={handleFileUpload}
                  disabled={!selectedFile || uploading}
                  className="w-full"
                >
                  {uploading ? 'Parsing...' : 'Parse File & Continue'}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Step 2: Field Mapping */}
          {step === 2 && parsedData && (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Step 2: Map Fields</CardTitle>
                    <CardDescription>
                      Map CSV columns to database fields ({getMappedCount()}/{fieldDefinitions.length} mapped)
                    </CardDescription>
                  </div>
                  <Button variant="outline" onClick={handleAutoMap}>
                    Auto-Map Fields
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Sample Data Preview */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">Preview Data ({parsedData.total_rows} total rows)</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr>
                          {parsedData.headers.map((header, i) => (
                            <th key={i} className="text-left p-2 bg-gray-200">{header}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {parsedData.sample_data.slice(0, 3).map((row, i) => (
                          <tr key={i} className="border-b">
                            {parsedData.headers.map((header, j) => (
                              <td key={j} className="p-2">{row[header]}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Field Mapping */}
                <div className="space-y-3">
                  <h4 className="font-semibold">Field Mapping</h4>
                  {fieldDefinitions.map(field => (
                    <div key={field.key} className="grid grid-cols-2 gap-4 items-center">
                      <div className="flex items-center space-x-2">
                        <Label className="font-medium">
                          {field.label}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </Label>
                      </div>
                      <Select
                        value={fieldMapping[field.key] || '__NONE__'}
                        onValueChange={(value) => setFieldMapping({ ...fieldMapping, [field.key]: value === '__NONE__' ? '' : value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select CSV column..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="__NONE__">-- Not Mapped --</SelectItem>
                          {parsedData.headers.map(header => (
                            <SelectItem key={header} value={header}>{header}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  ))}
                </div>

                <div className="flex space-x-2">
                  <Button variant="outline" onClick={resetImport}>Back</Button>
                  <Button
                    onClick={() => setStep(3)}
                    disabled={!getRequiredMapped()}
                    className="flex-1"
                  >
                    Review & Import
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <Card>
              <CardHeader>
                <CardTitle>Step 3: Review & Confirm</CardTitle>
                <CardDescription>Review your import settings before proceeding</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Import Type:</span>
                    <span className="font-medium capitalize">{importType}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">File:</span>
                    <span className="font-medium">{parsedData.filename}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Total Rows:</span>
                    <span className="font-medium">{parsedData.total_rows}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Fields Mapped:</span>
                    <span className="font-medium">{getMappedCount()}/{fieldDefinitions.length}</span>
                  </div>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                  <h4 className="font-semibold mb-3 flex items-center">
                    <Shield className="h-5 w-5 mr-2" />
                    Duplicate Protection
                  </h4>
                  <p className="text-sm text-gray-600 mb-3">
                    How should we handle duplicate members (based on email, phone, or name)?
                  </p>
                  <Select value={duplicateAction} onValueChange={setDuplicateAction}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="skip">
                        <div className="flex flex-col">
                          <span className="font-medium">Skip Duplicates</span>
                          <span className="text-xs text-gray-500">Don't import records that already exist</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="update">
                        <div className="flex flex-col">
                          <span className="font-medium">Update Existing</span>
                          <span className="text-xs text-gray-500">Update existing records with new data</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="create">
                        <div className="flex flex-col">
                          <span className="font-medium">Create Anyway</span>
                          <span className="text-xs text-gray-500">Create duplicate records (not recommended)</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">Field Mapping Summary</h4>
                  <div className="space-y-1 text-sm">
                    {fieldDefinitions.filter(f => fieldMapping[f.key]).map(field => (
                      <div key={field.key} className="flex justify-between">
                        <span className="text-gray-600">{field.label}:</span>
                        <span className="font-medium">{fieldMapping[field.key]}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button variant="outline" onClick={() => setStep(2)}>Back to Mapping</Button>
                  <Button
                    onClick={handleImport}
                    disabled={importing}
                    className="flex-1"
                  >
                    {importing ? 'Importing...' : `Import ${parsedData.total_rows} Records`}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 4: Complete */}
          {step === 4 && importResult && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                  <span>Import Complete</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="bg-green-50">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Created</p>
                        <p className="text-3xl font-bold text-green-600">{importResult.successful}</p>
                      </div>
                    </CardContent>
                  </Card>
                  {importResult.updated > 0 && (
                    <Card className="bg-blue-50">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-sm text-gray-600">Updated</p>
                          <p className="text-3xl font-bold text-blue-600">{importResult.updated}</p>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  {importResult.skipped > 0 && (
                    <Card className="bg-yellow-50">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-sm text-gray-600">Skipped</p>
                          <p className="text-3xl font-bold text-yellow-600">{importResult.skipped}</p>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  <Card className="bg-red-50">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Failed</p>
                        <p className="text-3xl font-bold text-red-600">{importResult.failed}</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {importResult.error_log && importResult.error_log.length > 0 && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 flex items-center">
                      <AlertCircle className="h-4 w-4 mr-2" />
                      Import Details (showing first 20)
                    </h4>
                    <div className="space-y-2 text-sm max-h-60 overflow-y-auto">
                      {importResult.error_log.map((log, i) => (
                        <div 
                          key={i} 
                          className={`p-2 rounded ${
                            log.action === 'skipped' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                          }`}
                        >
                          Row {log.row}: {log.reason || log.error}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Button onClick={resetImport} className="w-full">
                  Import More Data
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <History className="h-5 w-5" />
                <span>Import History</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingLogs ? (
                <div className="text-center py-8">Loading...</div>
              ) : importLogs.length === 0 ? (
                <div className="text-center py-8 text-gray-600">No imports yet</div>
              ) : (
                <div className="space-y-3">
                  {importLogs.map(log => (
                    <Card key={log.id} className="border-l-4 border-l-blue-500">
                      <CardContent className="py-3">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <Badge className="capitalize">{log.import_type}</Badge>
                              <span className="font-medium">{log.filename}</span>
                            </div>
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <span>Total: {log.total_rows}</span>
                              <span className="text-green-600">Success: {log.successful_rows}</span>
                              <span className="text-red-600">Failed: {log.failed_rows}</span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              {new Date(log.created_at).toLocaleString()}
                            </p>
                          </div>
                          <Badge variant={log.status === 'completed' ? 'default' : 'destructive'}>
                            {log.status}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default DataImport;
