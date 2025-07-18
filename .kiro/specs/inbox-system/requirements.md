# Requirements Document

## Introduction

This document outlines the requirements for implementing an inbox system that allows different user roles to manage and transfer applications/requests. The system enables role-based application management where applications can be viewed, processed, and transferred between roles while maintaining proper ownership tracking and bilingual support.

## Requirements

### Requirement 1

**User Story:** As a manager/controller, I want to view all applications assigned to my role in an inbox, so that I can efficiently manage and process pending requests.

#### Acceptance Criteria

1. WHEN a user with manager/controller role accesses their inbox THEN the system SHALL display all applications currently assigned to their role
2. WHEN displaying inbox content THEN the system SHALL show application details including client information, request type, and creation date
3. WHEN the inbox is empty THEN the system SHALL display an appropriate message indicating no pending applications
4. WHEN applications are displayed THEN the system SHALL support both Uzbek and Russian languages based on user preference

### Requirement 2

**User Story:** As a manager, I want to transfer applications to other roles (like junior manager), so that I can delegate work and ensure proper workflow distribution.

#### Acceptance Criteria

1. WHEN a manager selects an application from their inbox THEN the system SHALL provide options to transfer it to appropriate roles
2. WHEN an application is transferred to another role THEN the system SHALL update the application's ownership in the database
3. WHEN an application is transferred THEN the system SHALL remove it from the current role's inbox
4. WHEN an application is transferred THEN the system SHALL add it to the target role's inbox
5. WHEN transfer is completed THEN the system SHALL ensure the application exists in only one role's inbox

### Requirement 3

**User Story:** As a client, I want my applications to be automatically assigned to the appropriate role when created, so that they can be processed efficiently.

#### Acceptance Criteria

1. WHEN a client creates a new application THEN the system SHALL automatically assign it to the appropriate manager/controller role
2. WHEN an application is created THEN the system SHALL send a notification to the assigned role about the new application
3. WHEN assigning applications THEN the system SHALL update the database with the current role ownership
4. WHEN applications are created THEN the system SHALL ensure they appear in the assigned role's inbox immediately

### Requirement 4

**User Story:** As a role-based user (except client and admin), I want to access an inbox feature, so that I can manage applications assigned to my role.

#### Acceptance Criteria

1. WHEN a user belongs to manager, junior_manager, technician, warehouse, call_center, call_center_supervisor, or controller roles THEN the system SHALL provide inbox functionality
2. WHEN client or admin users try to access inbox THEN the system SHALL not provide this functionality
3. WHEN users access inbox THEN the system SHALL display role-specific applications only
4. WHEN inbox is accessed THEN the system SHALL support bilingual interface (Uzbek/Russian)

### Requirement 5

**User Story:** As a system administrator, I want applications to have proper ownership tracking in the database, so that the system can maintain data integrity and prevent applications from being lost or duplicated across roles.

#### Acceptance Criteria

1. WHEN an application is created THEN the system SHALL store the current assigned role in a dedicated database column
2. WHEN an application is transferred THEN the system SHALL update the assigned role column atomically
3. WHEN querying applications for a role THEN the system SHALL filter based on the assigned role column
4. WHEN an application exists THEN the system SHALL ensure it is assigned to exactly one role at any time
5. IF an application transfer fails THEN the system SHALL maintain the previous role assignment

### Requirement 6

**User Story:** As a user, I want the inbox interface to support both Uzbek and Russian languages, so that I can use the system in my preferred language.

#### Acceptance Criteria

1. WHEN displaying inbox content THEN the system SHALL show text in the user's selected language
2. WHEN showing application counts THEN the system SHALL use localized number formatting and labels
3. WHEN displaying empty inbox messages THEN the system SHALL show appropriate text in the selected language
4. WHEN showing transfer options THEN the system SHALL display role names and actions in the selected language
