import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ChevronLeftIcon, ChevronRightIcon, MagnifyingGlassIcon, FunnelIcon, ArrowUpIcon, ArrowDownIcon, XMarkIcon, CheckIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

// Types
interface BankData {
  BANK: string;
  IFSC: string;
  BRANCH: string;
  CENTRE: string;
  STATE: string;
  ADDRESS: string;
  CONTACT: string;
  IMPS: string;
  RTGS: string;
  CITY: string;
  ISO3166: string;
  NEFT: string;
  MICR: string;
  UPI: string;
  SWIFT: string;
}

interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

interface PaginationInfo {
  page: number;
  size: number;
  total_records: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

interface ApiResponse {
  file_info: {
    file_name: string;
    file_type: string;
    total_records_in_file: number;
    columns: string[];
  };
  data: BankData[];
  pagination: PaginationInfo;
  filters_applied: Record<string, any>;
  summary: {
    unique_banks: number;
    unique_states: number;
    unique_cities: number;
    payment_methods: Record<string, number>;
  };
}

type SortOrder = 'asc' | 'desc';

// Multi-select dropdown component
interface MultiSelectProps {
  label: string;
  field: string;
  selected: string[];
  onSelectionChange: (field: string, values: string[]) => void;
  placeholder?: string;
  apiBaseUrl: string;
}

const MultiSelectDropdown: React.FC<MultiSelectProps> = ({
  label,
  field,
  selected,
  onSelectionChange,
  placeholder = 'Select options...',
  apiBaseUrl
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [options, setOptions] = useState<FilterOption[]>([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch options from API
  const fetchOptions = useCallback(async (search?: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      params.append('limit', '200');

      const response = await fetch(`${apiBaseUrl}/banks/filter-options/${field}?${params}`);
      if (response.ok) {
        const data = await response.json();
        setOptions(data.options || []);
      }
    } catch (error) {
      console.error(`Error fetching ${field} options:`, error);
    } finally {
      setLoading(false);
    }
  }, [field, apiBaseUrl]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isOpen) {
        fetchOptions(searchTerm);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm, isOpen, fetchOptions]);

  // Initial load
  useEffect(() => {
    if (isOpen && options.length === 0) {
      fetchOptions();
    }
  }, [isOpen, options.length, fetchOptions]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggleOption = (value: string) => {
    const newSelected = selected.includes(value)
      ? selected.filter(item => item !== value)
      : [...selected, value];
    
    onSelectionChange(field, newSelected);
  };

  const handleSelectAll = () => {
    const allValues = options.map(option => option.value);
    onSelectionChange(field, allValues);
  };

  const handleClearAll = () => {
    onSelectionChange(field, []);
  };

  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
      
      {/* Dropdown trigger */}
      <div
        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md cursor-pointer focus:ring-1 focus:ring-blue-500 bg-white"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 truncate">
            {selected.length === 0 ? (
              <span className="text-gray-400">{placeholder}</span>
            ) : (
              <span className="text-gray-900">
                {selected.length === 1 
                  ? selected[0]
                  : `${selected.length} selected`
                }
              </span>
            )}
          </div>
          <ChevronDownIcon className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {/* Selected items display */}
      {selected.length > 0 && (
        <div className="mt-1 flex flex-wrap gap-1">
          {selected.slice(0, 3).map(item => (
            <span
              key={item}
              className="inline-flex items-center px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-md"
            >
              {item}
              <XMarkIcon
                className="w-3 h-3 ml-1 cursor-pointer hover:text-blue-600"
                onClick={(e) => {
                  e.stopPropagation();
                  handleToggleOption(item);
                }}
              />
            </span>
          ))}
          {selected.length > 3 && (
            <span className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-md">
              +{selected.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Dropdown menu */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-80 overflow-hidden">
          {/* Search box */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8 pr-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="p-2 border-b border-gray-200 bg-gray-50">
            <div className="flex gap-2">
              <button
                onClick={handleSelectAll}
                className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                Select All ({filteredOptions.length})
              </button>
              <button
                onClick={handleClearAll}
                className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                Clear All
              </button>
            </div>
          </div>

          {/* Options list */}
          <div className="overflow-y-auto max-h-60">
            {loading ? (
              <div className="p-3 text-center text-sm text-gray-500">
                Loading options...
              </div>
            ) : filteredOptions.length === 0 ? (
              <div className="p-3 text-center text-sm text-gray-500">
                No options found
              </div>
            ) : (
              filteredOptions.map(option => (
                <div
                  key={option.value}
                  className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleToggleOption(option.value)}
                >
                  <div className="flex items-center min-w-0 flex-1">
                    <div className={`w-4 h-4 border border-gray-300 rounded mr-2 flex items-center justify-center ${
                      selected.includes(option.value) ? 'bg-blue-600 border-blue-600' : 'bg-white'
                    }`}>
                      {selected.includes(option.value) && (
                        <CheckIcon className="w-3 h-3 text-white" />
                      )}
                    </div>
                    <span className="text-sm text-gray-900 truncate flex-1">
                      {option.label}
                    </span>
                    {option.count && (
                      <span className="text-xs text-gray-500 ml-2">
                        ({option.count})
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const BankDataTable: React.FC = () => {
  // State management
  const [bankData, setBankData] = useState<BankData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [apiResponse, setApiResponse] = useState<ApiResponse | null>(null);

  // Updated filters to support multiple selections
  const [filters, setFilters] = useState({
    bank: [] as string[],
    state: [] as string[],
    city: [] as string[],
    branch: [] as string[],
    centre: [] as string[],
    ifsc: '',
    micr: '',
    address: '',
    contact: '',
    swift: '',
    iso3166: '',
    imps_enabled: undefined as boolean | undefined,
    rtgs_enabled: undefined as boolean | undefined,
    neft_enabled: undefined as boolean | undefined,
    upi_enabled: undefined as boolean | undefined,
  });

  // Search and pagination states
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [sortBy, setSortBy] = useState('BANK');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [showFilters, setShowFilters] = useState(false);

  const API_BASE_URL = '/api';

  // Fetch data function
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      // Add search parameter
      if (search.trim()) {
        params.append('search', search.trim());
      }

      // Add multi-value filter parameters
      filters.bank.forEach(value => params.append('bank', value));
      filters.state.forEach(value => params.append('state', value));
      filters.city.forEach(value => params.append('city', value));
      filters.branch.forEach(value => params.append('branch', value));
      filters.centre.forEach(value => params.append('centre', value));

      // Add single-value filter parameters
      if (filters.ifsc) params.append('ifsc', filters.ifsc);
      if (filters.micr) params.append('micr', filters.micr);
      if (filters.address) params.append('address', filters.address);
      if (filters.contact) params.append('contact', filters.contact);
      if (filters.swift) params.append('swift', filters.swift);
      if (filters.iso3166) params.append('iso3166', filters.iso3166);

      // Add boolean filter parameters
      if (filters.imps_enabled !== undefined) {
        params.append('imps_enabled', filters.imps_enabled.toString());
      }
      if (filters.rtgs_enabled !== undefined) {
        params.append('rtgs_enabled', filters.rtgs_enabled.toString());
      }
      if (filters.neft_enabled !== undefined) {
        params.append('neft_enabled', filters.neft_enabled.toString());
      }
      if (filters.upi_enabled !== undefined) {
        params.append('upi_enabled', filters.upi_enabled.toString());
      }

      const response = await fetch(`${API_BASE_URL}/banks/?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      setBankData(data.data);
      setApiResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setBankData([]);
      setApiResponse(null);
    } finally {
      setLoading(false);
    }
  }, [page, size, sortBy, sortOrder, search, filters]);

  // Effect to fetch data when dependencies change
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Reset to first page when filters change
  useEffect(() => {
    if (page !== 1) {
      setPage(1);
    }
  }, [search, filters]);

  // Handler functions
  const handleMultiSelectChange = (field: string, values: string[]) => {
    setFilters(prev => ({
      ...prev,
      [field]: values
    }));
  };

  const handleSingleFilterChange = (key: keyof typeof filters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === '' ? undefined : value
    }));
  };

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  const clearFilters = () => {
    setFilters({
      bank: [],
      state: [],
      city: [],
      branch: [],
      centre: [],
      ifsc: '',
      micr: '',
      address: '',
      contact: '',
      swift: '',
      iso3166: '',
      imps_enabled: undefined,
      rtgs_enabled: undefined,
      neft_enabled: undefined,
      upi_enabled: undefined,
    });
    setSearch('');
    setPage(1);
  };

  const handlePageSizeChange = (newSize: number) => {
    setSize(newSize);
    setPage(1);
  };

  // Render sort icon
  const renderSortIcon = (column: string) => {
    if (sortBy !== column) return null;
    return sortOrder === 'asc' ? 
      <ArrowUpIcon className="w-4 h-4 ml-1" /> : 
      <ArrowDownIcon className="w-4 h-4 ml-1" />;
  };

  // Check if any filters are applied
  const hasActiveFilters = () => {
    return (
      filters.bank.length > 0 ||
      filters.state.length > 0 ||
      filters.city.length > 0 ||
      filters.branch.length > 0 ||
      filters.centre.length > 0 ||
      filters.ifsc !== '' ||
      filters.micr !== '' ||
      filters.address !== '' ||
      filters.contact !== '' ||
      filters.swift !== '' ||
      filters.iso3166 !== '' ||
      filters.imps_enabled !== undefined ||
      filters.rtgs_enabled !== undefined ||
      filters.neft_enabled !== undefined ||
      filters.upi_enabled !== undefined ||
      search !== ''
    );
  };

  // Pagination component (same as before)
  const renderPagination = () => {
    if (!apiResponse?.pagination) return null;

    const { pagination } = apiResponse;
    const totalPages = pagination.total_pages;
    const currentPage = pagination.page;

    const getPageNumbers = () => {
      const pages = [];
      const maxVisible = 5;
      
      if (totalPages <= maxVisible) {
        for (let i = 1; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        if (currentPage <= 3) {
          for (let i = 1; i <= 5; i++) {
            pages.push(i);
          }
        } else if (currentPage >= totalPages - 2) {
          for (let i = totalPages - 4; i <= totalPages; i++) {
            pages.push(i);
          }
        } else {
          for (let i = currentPage - 2; i <= currentPage + 2; i++) {
            pages.push(i);
          }
        }
      }
      
      return pages;
    };

    return (
      <div className="flex items-center justify-between px-6 py-3 bg-white border-t border-gray-200">
        <div className="flex items-center text-sm text-gray-700">
          <span>
            Showing {((currentPage - 1) * pagination.size) + 1} to{' '}
            {Math.min(currentPage * pagination.size, pagination.total_records)} of{' '}
            {pagination.total_records} results
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPage(currentPage - 1)}
            disabled={!pagination.has_prev}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeftIcon className="w-5 h-5" />
          </button>
          
          {getPageNumbers().map(pageNum => (
            <button
              key={pageNum}
              onClick={() => setPage(pageNum)}
              className={`px-3 py-1 text-sm border rounded-md ${
                pageNum === currentPage
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'border-gray-300 hover:bg-gray-50'
              }`}
            >
              {pageNum}
            </button>
          ))}
          
          <button
            onClick={() => setPage(currentPage + 1)}
            disabled={!pagination.has_next}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 bg-white">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Bank Data Management Tool</h1>
      </div>

      {/* Search and Controls */}
      <div className="mb-6 space-y-4">
        {/* Search Bar and Controls Row */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          {/* Search Input */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search across all fields..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center px-3 py-2 text-sm border rounded-lg ${
                showFilters ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-gray-300 hover:bg-gray-50'
              }`}
            >
              <FunnelIcon className="w-4 h-4 mr-2" />
              Filters
              {hasActiveFilters() && (
                <span className="ml-2 px-1.5 py-0.5 text-xs bg-blue-600 text-white rounded-full">
                  •
                </span>
              )}
            </button>

            <select
              value={size}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value={10}>10 per page</option>
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>

            {hasActiveFilters() && (
              <button
                onClick={clearFilters}
                className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Clear All
              </button>
            )}
          </div>
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {/* Multi-select filters */}
              <MultiSelectDropdown
                label="Bank"
                field="bank"
                selected={filters.bank}
                onSelectionChange={handleMultiSelectChange}
                placeholder="Select banks..."
                apiBaseUrl={API_BASE_URL}
              />

              <MultiSelectDropdown
                label="State"
                field="state"
                selected={filters.state}
                onSelectionChange={handleMultiSelectChange}
                placeholder="Select states..."
                apiBaseUrl={API_BASE_URL}
              />

              <MultiSelectDropdown
                label="City"
                field="city"
                selected={filters.city}
                onSelectionChange={handleMultiSelectChange}
                placeholder="Select cities..."
                apiBaseUrl={API_BASE_URL}
              />


              {/* Text input filters */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">IFSC</label>
                <input
                  type="text"
                  placeholder="Filter by IFSC"
                  value={filters.ifsc}
                  onChange={(e) => handleSingleFilterChange('ifsc', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* Payment Method Filters */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">IMPS</label>
                <select
                  value={filters.imps_enabled === undefined ? '' : filters.imps_enabled.toString()}
                  onChange={(e) => handleSingleFilterChange('imps_enabled', e.target.value === '' ? undefined : e.target.value === 'true')}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">RTGS</label>
                <select
                  value={filters.rtgs_enabled === undefined ? '' : filters.rtgs_enabled.toString()}
                  onChange={(e) => handleSingleFilterChange('rtgs_enabled', e.target.value === '' ? undefined : e.target.value === 'true')}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">UPI</label>
                <select
                  value={filters.upi_enabled === undefined ? '' : filters.upi_enabled.toString()}
                  onChange={(e) => handleSingleFilterChange('upi_enabled', e.target.value === '' ? undefined : e.target.value === 'true')}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      {apiResponse?.summary && (
        <div className="mb-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{apiResponse.summary.unique_banks}</div>
            <div className="text-xs text-blue-600">Banks</div>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{apiResponse.summary.unique_states}</div>
            <div className="text-xs text-green-600">States</div>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{apiResponse.summary.payment_methods.imps_enabled || 0}</div>
            <div className="text-xs text-purple-600">IMPS</div>
          </div>
          <div className="bg-yellow-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{apiResponse.summary.payment_methods.rtgs_enabled || 0}</div>
            <div className="text-xs text-yellow-600">RTGS</div>
          </div>
          <div className="bg-red-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{apiResponse.summary.payment_methods.neft_enabled || 0}</div>
            <div className="text-xs text-red-600">NEFT</div>
          </div>
          <div className="bg-indigo-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-indigo-600">{apiResponse.summary.payment_methods.upi_enabled || 0}</div>
            <div className="text-xs text-indigo-600">UPI</div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading bank data...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800 font-medium">Error loading data</div>
          <div className="text-red-600 text-sm mt-1">{error}</div>
          <button
            onClick={fetchData}
            className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      )}

      {/* Data Table */}
      {!loading && !error && (
        <div className="bg-white shadow-lg rounded-lg overflow-hidden border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {['BANK', 'IFSC', 'BRANCH', 'CITY', 'STATE' , 'IMPS', 'RTGS', 'NEFT', 'UPI'].map((column) => (
                    <th
                      key={column}
                      onClick={() => handleSort(column)}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div className="flex items-center">
                        {column}
                        {renderSortIcon(column)}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {bankData.map((bank, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {bank.BANK}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {bank.IFSC}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {bank.BRANCH}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {bank.CITY}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {bank.STATE}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        bank.IMPS === 'Y' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {bank.IMPS === 'Y' ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        bank.RTGS === 'Y' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {bank.RTGS === 'Y' ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        bank.NEFT === 'Y' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {bank.NEFT === 'Y' ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        bank.UPI === 'Y' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {bank.UPI === 'Y' ? 'Yes' : 'No'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {renderPagination()}
        </div>
      )}

      {/* No Data State */}
      {!loading && !error && bankData.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">No bank data found</div>
          <div className="text-gray-400 text-sm mt-2">
            Try adjusting your search or filter criteria
          </div>
        </div>
      )}
    </div>
  );
};

export default BankDataTable;
