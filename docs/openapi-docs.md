# OpenAPI Documentation

This page contains the complete OpenAPI specification for the StatusPro Manufacturing
ERP API, rendered with Swagger UI for interactive exploration.

## About the StatusPro API

The StatusPro API provides programmatic access to your StatusPro Manufacturing ERP
system, allowing you to:

- **Manage Products**: Create, read, update, and delete products and variants
- **Inventory Control**: Track inventory levels, movements, and locations
- **Manufacturing Orders**: Create and manage manufacturing orders and operations
- **Purchase Orders**: Handle supplier relationships and purchase order management
- **Sales Orders**: Process customer orders and fulfillment
- **And Much More**: Complete access to all StatusPro functionality

## Interactive API Explorer

Use the interactive API explorer below to:

- **Browse endpoints** organized by category
- **View request/response schemas** with detailed type information
- **Test API calls** directly from the documentation (with proper authentication)
- **Explore examples** for each endpoint

!!! tip "API Authentication" To test API calls through this interface, you'll need to:

```
1. Click the **Authorize** button in the Swagger UI below
2. Enter your API key in the format: `Bearer YOUR_API_KEY_HERE`
3. Your API key can be found in your StatusPro account settings
```

!!! info "Base URLs" - **Production**: `https://app.orderstatuspro.com/api/v1` -
**Demo/Testing**: Use your specific StatusPro instance URL

---

<swagger-ui src="statuspro-openapi.yaml"/>

## Need Help?

- **Client Documentation**: See our [StatusProClient Guide](client/guide.md) for
  Python-specific usage
- **Rate Limiting**: The API has rate limits - our client handles this automatically
- **Pagination**: Large result sets are paginated - our client auto-paginates
- **Error Handling**: See the API responses above for error codes and messages

## OpenAPI Specification

The complete OpenAPI specification is available at:
[`statuspro-openapi.yaml`](statuspro-openapi.yaml)

This specification includes:

- **100+ API endpoints** across all StatusPro modules
- **Complete request/response schemas** with validation rules
- **Authentication requirements** for each endpoint
- **Real-world examples** for all operations
