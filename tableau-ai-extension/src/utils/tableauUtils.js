/**
 * Utility functions for working with Tableau Extensions API
 */

/**
 * Determines if a worksheet is a map visualization
 * @param {Object} worksheet - Tableau worksheet object
 * @returns {boolean} - True if the worksheet appears to be a map
 */
/**
 * Determines if a worksheet is a map visualization based on its name
 * @param {Object} worksheet - Tableau worksheet object
 * @returns {boolean} - True if the worksheet appears to be a map
 */
const isMapVisualization = (worksheet) => {
  try {
    // Check worksheet name first
    const nameHints = ['map', 'geo', 'location', 'region', 'spatial'];
    const name = worksheet.name.toLowerCase();
    if (nameHints.some(hint => name.includes(hint))) {
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('Error checking if worksheet is a map:', error);
    return false;
  }
};

/**
 * Checks if a worksheet contains geographical data by examining column names
 * @param {Object} worksheet - Tableau worksheet object
 * @returns {Promise<boolean>} - True if the worksheet contains geographical columns
 */
const checkForGeographicalData = async (worksheet) => {
  try {
    // Get the fields from the worksheet
    const fields = await worksheet.getFieldsAsync();
    
    // Check if any fields have names suggesting geographical data
    const geoFieldHints = [
      'latitude', 'longitude', ' lat', ' lon', ' lng', 
      'geolocation', 'coordinate', 'postal', 'zip', 
      'address', 'street', 'city', 'state', 'country'
    ];
    
    // Look for geographical field names
    for (const field of fields) {
      const fieldName = field.name.toLowerCase();
      
      // Check for geographical hints in the field name
      if (geoFieldHints.some(hint => fieldName.includes(hint))) {
        console.log(`Found geographical field: ${field.name}`);
        return true;
      }
      
      // Check for spatial data type
      if (field.dataType === 'spatial') {
        console.log(`Found spatial data type in field: ${field.name}`);
        return true;
      }
    }
    
    return false;
  } catch (error) {
    console.error('Error checking for geographical data:', error);
    return false;
  }
};

/**
 * Fetches data from the specified worksheet
 * @param {Object} worksheet - Tableau worksheet object
 * @param {boolean} includeAllColumns - Whether to include all columns or just those in the view
 * @returns {Promise<Object>} - Formatted data object
 */
export const getWorksheetData = async (worksheet, includeAllColumns = true) => {
  try {
    // Check if this is a map/geographical worksheet
    let isMapWorksheet = isMapVisualization(worksheet);
    
    // Get column information to check for geo columns
    const hasGeoData = await checkForGeographicalData(worksheet);
    
    // If the worksheet has geo columns, consider it a map
    if (hasGeoData) {
      isMapWorksheet = true;
    }
    
    console.log(`Worksheet ${worksheet.name} is map visualization: ${isMapWorksheet} (has geo data: ${hasGeoData})`);
    
    // Get the summary data (includes all columns shown in the view)
    const summaryDataOptions = {
      ignoreSelection: false,
      includeAllColumns: includeAllColumns,
      maxRows: isMapWorksheet ? 100 : 10000 // Lower limit for maps to avoid huge payloads
    };
    
    const dataTable = await worksheet.getSummaryDataAsync(summaryDataOptions);
    
    // Format the data in a more friendly structure
    const data = {
      sheetName: worksheet.name,
      isMap: isMapWorksheet,
      columns: dataTable.columns.map(column => ({
        fieldName: column.fieldName,
        dataType: column.dataType,
        isReferenced: column.isReferenced
      })),
      rows: []
    };
    
    // Detect geographical columns we want to exclude
    const geoColumns = [];
    const shouldExcludeMap = isMapWorksheet;
    
    // Identify geographical columns by name or data type
    if (shouldExcludeMap) {
      for (let j = 0; j < dataTable.columns.length; j++) {
        const column = dataTable.columns[j];
        const colName = column.fieldName.toLowerCase();
        
        // Match against common geospatial column names
        if (
          colName.includes('latitude') || 
          colName.includes('longitude') || 
          colName.includes('lat') || 
          colName.includes('lng') || 
          colName.includes('lon') ||
          colName.includes('geolocation') ||
          colName.includes('coordinate') ||
          column.dataType === 'spatial'
        ) {
          geoColumns.push(column.fieldName);
          console.log(`Identified geographical column: ${column.fieldName}`);
        }
      }
    }
    
    // As per requirement, completely exclude map worksheets and geo data
    if (isMapWorksheet) {
      // For map worksheets, just return minimal metadata without any rows
      data.rows = [];
      data.note = "This worksheet contains geographical data and has been completely excluded.";
      data.excluded = true;
      
      // Log that we're excluding this worksheet
      console.log(`Excluding map worksheet: ${worksheet.name}`);
      
      return data;
    }
    
    // First, analyze the data to identify redundant patterns and optimize structure
    // Create a column name mapping to use shorter field names for repeated long identifiers
    const columnNameMapping = {};
    const longFieldNamePattern = /\[federated\.[a-z0-9]+\]\.\[[^\]]+\]/;
    
    for (let j = 0; j < dataTable.columns.length; j++) {
      const column = dataTable.columns[j];
      const colName = column.fieldName;
      
      // Skip geographical columns
      const lowerColName = colName.toLowerCase();
      if (
        lowerColName.includes('latitude') || 
        lowerColName.includes('longitude') || 
        lowerColName.includes('lat') || 
        lowerColName.includes('lng') || 
        lowerColName.includes('lon') ||
        lowerColName.includes('geolocation') ||
        lowerColName.includes('coordinate') ||
        lowerColName.includes('address') ||
        lowerColName.includes('street') ||
        lowerColName.includes('city') ||
        lowerColName.includes('state') ||
        lowerColName.includes('country') ||
        lowerColName.includes('postal') ||
        lowerColName.includes('zip') ||
        column.dataType === 'spatial'
      ) {
        // Skip this column entirely
        console.log(`Excluding geographical column: ${column.fieldName}`);
        continue;
      }
      
      // Check if it's a long federated name that should be shortened
      if (longFieldNamePattern.test(colName)) {
        // Extract a shorter, more readable name from the field
        let shortName = colName;
        
        // Try to find actual measure name from brackets
        const bracketMatch = colName.match(/\[([^\]]+)\]/g);
        if (bracketMatch && bracketMatch.length > 1) {
          // Use the last bracketed segment but clean it up
          shortName = bracketMatch[bracketMatch.length - 1].replace(/[\[\]]/g, '');
          
          // Further clean up common suffixes from Tableau's naming
          shortName = shortName
            .replace(/_\d+:qk$/, '')
            .replace(/:qk$/, '')
            .replace(/sum:/, '')
            .replace(/usr:/, '')
            .replace(/ATTR\(([^)]+)\)/, '$1');
        }
        
        columnNameMapping[colName] = shortName;
        console.log(`Mapping column "${colName}" to "${shortName}"`);
      } else {
        // No mapping needed for already short names
        columnNameMapping[colName] = colName;
      }
    }
    
    // Add the column mapping to the data for reference
    data.columnMapping = columnNameMapping;
    
    // Look for values that repeat across many rows (like constants or categorical values)
    const valueFrequency = {};
    const columnValues = {};
    
    // First pass: collect all unique values per column to identify constants
    for (let j = 0; j < dataTable.columns.length; j++) {
      const column = dataTable.columns[j];
      const colName = column.fieldName;
      
      // Skip if geographical
      const lowerColName = colName.toLowerCase();
      if (
        lowerColName.includes('latitude') || 
        lowerColName.includes('longitude') || 
        lowerColName.includes('lat') || 
        lowerColName.includes('lng') || 
        lowerColName.includes('lon') ||
        lowerColName.includes('geolocation') ||
        lowerColName.includes('coordinate') ||
        lowerColName.includes('address') ||
        lowerColName.includes('street') ||
        lowerColName.includes('city') ||
        lowerColName.includes('state') ||
        lowerColName.includes('country') ||
        lowerColName.includes('postal') ||
        lowerColName.includes('zip') ||
        column.dataType === 'spatial'
      ) {
        continue;
      }
      
      columnValues[colName] = new Set();
      
      // Count frequency of each value in this column
      for (let i = 0; i < dataTable.totalRowCount; i++) {
        const value = dataTable.data[i][j].value;
        columnValues[colName].add(value);
        
        const valueKey = `${colName}:${value}`;
        valueFrequency[valueKey] = (valueFrequency[valueKey] || 0) + 1;
      }
    }
    
    // Identify constant columns (single value across all rows)
    const constantColumns = {};
    for (const colName in columnValues) {
      if (columnValues[colName].size === 1) {
        // This column has the same value in all rows
        const value = Array.from(columnValues[colName])[0];
        constantColumns[colName] = value;
        console.log(`Constant column found: "${colName}" = "${value}"`);
      }
    }
    
    // Add constants to the data structure instead of repeating in each row
    data.constants = {};
    for (const colName in constantColumns) {
      const shortName = columnNameMapping[colName] || colName;
      data.constants[shortName] = constantColumns[colName];
    }
    
    // Determine if we need to sample the data
    const MAX_ROWS = 300; // Maximum number of rows to include
    const needsSampling = dataTable.totalRowCount > MAX_ROWS;
    
    // Apply sampling if needed - otherwise process all rows
    let rowsToProcess = [];
    let samplingInfo = null;
    
    if (needsSampling) {
      // Calculate a sampling rate to get approximately MAX_ROWS
      const samplingRate = Math.max(1, Math.floor(dataTable.totalRowCount / MAX_ROWS));
      samplingInfo = {
        totalRows: dataTable.totalRowCount,
        samplingRate: samplingRate, 
        sampledRows: Math.ceil(dataTable.totalRowCount / samplingRate)
      };
      
      // Select rows at regular intervals
      for (let i = 0; i < dataTable.totalRowCount; i += samplingRate) {
        rowsToProcess.push(i);
      }
      
      console.log(`Sampling data: ${samplingInfo.sampledRows} out of ${samplingInfo.totalRows} rows`);
    } else {
      // Use all rows
      for (let i = 0; i < dataTable.totalRowCount; i++) {
        rowsToProcess.push(i);
      }
    }
    
    // Add sampling information to the data
    if (samplingInfo) {
      data.sampling = samplingInfo;
      data.note = (data.note || '') + 
        `Dataset sampled: showing ${samplingInfo.sampledRows} out of ${samplingInfo.totalRows} total rows. `;
    }
    
    // For time series or regularly structured data, we can detect identical patterns
    // and collapse them to further save tokens
    data.patterns = [];
    
    // Process rows with optimized structure, excluding constants and using shortened names
    for (const i of rowsToProcess) {
      const row = {};
      for (let j = 0; j < dataTable.columns.length; j++) {
        const column = dataTable.columns[j];
        const colName = column.fieldName;
        
        // Skip geographical columns
        const lowerColName = colName.toLowerCase();
        if (
          lowerColName.includes('latitude') || 
          lowerColName.includes('longitude') || 
          lowerColName.includes('lat') || 
          lowerColName.includes('lng') || 
          lowerColName.includes('lon') ||
          lowerColName.includes('geolocation') ||
          lowerColName.includes('coordinate') ||
          lowerColName.includes('address') ||
          lowerColName.includes('street') ||
          lowerColName.includes('city') ||
          lowerColName.includes('state') ||
          lowerColName.includes('country') ||
          lowerColName.includes('postal') ||
          lowerColName.includes('zip') ||
          column.dataType === 'spatial'
        ) {
          continue;
        }
        
        // Skip constant columns, they're already in data.constants
        if (constantColumns[colName] !== undefined) {
          continue;
        }
        
        // Use the shorter field name and include only non-constant values
        const shortName = columnNameMapping[colName] || colName;
        row[shortName] = dataTable.data[i][j].value;
      }
      
      // Only add non-empty rows
      if (Object.keys(row).length > 0) {
        data.rows.push(row);
      }
    }
    
    // If we've filtered out geo columns but it's not a map worksheet, add a note
    if (geoColumns.length > 0) {
      data.note = (data.note || '') + `Geographical data (${geoColumns.join(', ')}) has been completely excluded. `;
    }
    
    // Check final data size and log warning if it's still large
    const dataJson = JSON.stringify(data);
    const dataSize = new Blob([dataJson]).size;
    const dataSizeKB = Math.round(dataSize / 1024);
    console.log(`Worksheet ${worksheet.name} data size: ${dataSizeKB} KB`);
    
    // If data is larger than 500KB, it might be too large for efficient processing
    if (dataSize > 500 * 1024) {
      console.warn(`Warning: Data for worksheet ${worksheet.name} is very large (${dataSizeKB} KB) even after optimization`);
      
      // Add warning to data for backend processing
      data.warning = `Large data size (${dataSizeKB} KB) - consider further filtering`;
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching worksheet data:', error);
    throw error;
  }
};

/**
 * Gets information about all fields in a worksheet
 * @param {Object} worksheet - Tableau worksheet object
 * @returns {Promise<Array>} - Array of field information
 */
export const getFieldInfo = async (worksheet) => {
  try {
    // Get all fields from the worksheet
    const fields = await worksheet.getFieldsAsync();
    
    // Format the fields information
    return fields.map(field => ({
      name: field.name,
      fieldType: field.fieldType,
      dataType: field.dataType,
      isHidden: field.isHidden,
      isGenerated: field.isGenerated,
      isCalculatedField: field.isCalculatedField
    }));
  } catch (error) {
    console.error('Error fetching field information:', error);
    throw error;
  }
};

/**
 * Gets all worksheets from the current dashboard
 * @returns {Array} - Array of Tableau worksheet objects
 */
export const getAllWorksheets = () => {
  try {
    const dashboard = window.tableau.extensions.dashboardContent.dashboard;
    return dashboard.worksheets;
  } catch (error) {
    console.error('Error getting worksheets:', error);
    return [];
  }
};

/**
 * Gets the selected marks from a worksheet
 * @param {Object} worksheet - Tableau worksheet object
 * @returns {Promise<Object>} - Selected marks data
 */
export const getSelectedMarks = async (worksheet) => {
  try {
    const marksInfo = await worksheet.getSelectedMarksAsync();
    
    // Format the selected marks data
    const data = {
      sheetName: worksheet.name,
      marksCount: marksInfo.data.length,
      columns: marksInfo.columns.map(column => ({
        fieldName: column.fieldName,
        dataType: column.dataType
      })),
      marks: []
    };
    
    // Process each mark
    for (let i = 0; i < marksInfo.data.length; i++) {
      const mark = {};
      for (let j = 0; j < marksInfo.columns.length; j++) {
        const column = marksInfo.columns[j];
        mark[column.fieldName] = marksInfo.data[i][j].value;
      }
      data.marks.push(mark);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching selected marks:', error);
    throw error;
  }
};