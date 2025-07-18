# Implementation Plan

- [x] 1. Set up database schema and core data models





  - Create database migration script to add role tracking columns to existing tables
  - Implement InboxMessage and ApplicationTransfer data models with validation
  - Create database indexes for efficient role-based queries
  - Write unit tests for data model validation and database operations
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2. Implement core inbox service layer





  - [x] 2.1 Create InboxService class with role-based application retrieval




    - Write get_role_applications method to query applications by assigned role
    - Implement application filtering logic for different application types (zayavka, service_request)
    - Add pagination support for large application lists
    - Write unit tests for application retrieval functionality
    - _Requirements: 1.1, 1.2, 4.3_



  - [ ] 2.2 Implement application transfer functionality
    - Write ApplicationTransferService class with transfer validation logic
    - Implement execute_transfer method with atomic database operations
    - Add transfer logging and audit trail functionality
    - Create rollback mechanism for failed transfers
    - Write unit tests for transfer operations and validation


    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.4_

  - [ ] 2.3 Add inbox message management
    - Implement create_inbox_message method for new application notifications
    - Write mark_as_read functionality for message status updates
    - Add message cleanup and archiving logic
    - Create unit tests for message management operations
    - _Requirements: 3.2, 1.3_

- [ ] 3. Create localization and text management system
  - Implement inbox-specific localization utilities with Uzbek and Russian support
  - Create dynamic text generation functions for application counts and status messages
  - Add role-specific text formatting for different application types
  - Write unit tests for localization functions and text rendering
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 4. Build role-specific keyboard generation
  - [ ] 4.1 Create inbox keyboard utilities
    - Write get_inbox_main_keyboard function for application listing
    - Implement get_application_actions_keyboard for individual application actions
    - Add get_transfer_options_keyboard for role transfer selection
    - Create pagination keyboard for large application lists
    - Write unit tests for keyboard generation functions
    - _Requirements: 1.1, 2.1, 4.1, 4.2, 4.3, 4.4_

  - [ ] 4.2 Integrate inbox buttons into existing role keyboards
    - Add "📥 Inbox" button to manager_buttons.py main keyboard
    - Add "📥 Inbox" button to junior_manager_buttons.py main keyboard
    - Add "📥 Inbox" button to controller_buttons.py main keyboard
    - Add "📥 Inbox" button to technician_buttons.py main keyboard
    - Add "📥 Inbox" button to warehouse_buttons.py main keyboard
    - Add "📥 Inbox" button to call_center_buttons.py main keyboard
    - Add "📥 Inbox" button to call_center_supervisor_buttons.py main keyboard
    - _Requirements: 4.1, 4.2_

- [ ] 5. Implement universal inbox handler
  - [ ] 5.1 Create main inbox handler class
    - Write InboxHandler class with role detection and application filtering
    - Implement show_inbox method with bilingual message formatting
    - Add error handling for invalid roles and database failures
    - Create unit tests for inbox display functionality
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.3, 6.1, 6.2, 6.3_

  - [ ] 5.2 Add application interaction handlers
    - Implement handle_application_selection for viewing application details
    - Write handle_transfer_request for processing role transfers
    - Add handle_mark_as_read for message status updates
    - Create callback query handlers for all inbox interactions
    - Write integration tests for handler workflows
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 6. Integrate with existing application creation workflows
  - [ ] 6.1 Update client application creation to assign to manager role
    - Modify client zayavka creation handlers to set assigned_role to 'manager'
    - Update service request creation to set role_current to appropriate initial role
    - Add inbox message creation when new applications are submitted
    - Write integration tests for application creation and role assignment
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 6.2 Add notification system integration
    - Integrate with existing notification system to send role-based notifications
    - Implement notification sending when applications are transferred between roles
    - Add notification cleanup when applications are processed
    - Write integration tests for notification workflows
    - _Requirements: 3.2, 2.4_

- [ ] 7. Create database query utilities
  - Write specialized database queries for role-based application filtering
  - Implement efficient JOIN queries for application details with user information
  - Add database utilities for atomic transfer operations
  - Create query optimization for large datasets with proper indexing
  - Write unit tests for all database query functions
  - _Requirements: 1.1, 2.3, 2.4, 5.1, 5.2, 5.3_

- [ ] 8. Implement error handling and validation
  - Create comprehensive error handling for invalid role transfers
  - Add validation for application existence and user permissions
  - Implement graceful error messages in both Uzbek and Russian
  - Add logging for debugging transfer failures and access issues
  - Write unit tests for error scenarios and validation logic
  - _Requirements: 2.5, 5.4, 5.5_

- [ ] 9. Add router registration and middleware integration
  - Register inbox handler router with the main application
  - Integrate with existing role-based middleware for access control
  - Add inbox functionality to universal router for all eligible roles
  - Update main.py to include inbox handler registration
  - Write integration tests for router registration and middleware
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 10. Create comprehensive testing suite
  - [ ] 10.1 Write unit tests for all service classes
    - Test InboxService methods with various role and application scenarios
    - Test ApplicationTransferService with valid and invalid transfer cases
    - Test localization functions with both supported languages
    - Test keyboard generation with different application states
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 10.2 Create integration tests for end-to-end workflows
    - Test complete application creation to inbox assignment workflow
    - Test application transfer between different role combinations
    - Test bilingual interface functionality across all supported roles
    - Test error handling and recovery scenarios
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 11. Performance optimization and monitoring
  - Implement database query optimization with proper indexing
  - Add caching for frequently accessed application data
  - Create performance monitoring for inbox loading times
  - Optimize memory usage for large application lists with pagination
  - Write performance tests to validate optimization improvements
  - _Requirements: 1.1, 1.2, 4.3_

- [ ] 12. Final integration and deployment preparation
  - Integrate all inbox components with existing bot infrastructure
  - Update configuration files and environment settings
  - Create deployment scripts for database migrations
  - Perform end-to-end testing in staging environment
  - Document inbox system usage and troubleshooting guide
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_