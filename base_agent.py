#!/usr/bin/env python3
"""
BaseAgent - Abstract base class for all WP2ASTRO migration agents.

This module provides common functionality and interfaces that all migration agents
should implement, including logging, error handling, result models, and validation.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# Type variable for generic result types
T = TypeVar('T')


class AgentStatus(str, Enum):
    """Status enumeration for agent operations."""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class BaseResult(BaseModel, Generic[T]):
    """Base result model for all agent operations."""
    success: bool
    status: AgentStatus
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[T] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class AgentMetrics(BaseModel):
    """Metrics tracking for agent operations."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    last_operation_time: Optional[datetime] = None
    
    def update_metrics(self, success: bool, execution_time: float):
        """Update metrics after an operation."""
        self.total_operations += 1
        self.total_execution_time += execution_time
        self.last_operation_time = datetime.now()
        
        if success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
        
        self.average_execution_time = self.total_execution_time / self.total_operations


class BaseAgent(ABC):
    """Abstract base class for all migration agents."""
    
    def __init__(self, name: Optional[str] = None, **kwargs):
        """Initialize the base agent.
        
        Args:
            name: Optional custom name for the agent
            **kwargs: Additional configuration parameters
        """
        # Set agent name (default to class name if not provided)
        self.name = name or self.__class__.__name__
        
        # Agent configuration (must be set before logging setup)
        self.config = kwargs
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Initialize metrics
        self.metrics = AgentMetrics()
        
        # Current status
        self.status = AgentStatus.IDLE
        
        # Validation settings
        self.validate_inputs = kwargs.get('validate_inputs', True)
        self.validate_outputs = kwargs.get('validate_outputs', True)
        
        self.logger.info(f"Initialized {self.name}")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the agent."""
        logger = logging.getLogger(f"{self.__module__}.{self.name}")
        
        # Set level from config or default to INFO
        log_level = self.config.get('log_level', 'INFO')
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Add handler if none exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _execute_with_metrics(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute an operation with metrics tracking and error handling.
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            BaseResult with operation results
        """
        self.logger.info(f"Starting {operation_name}")
        self.status = AgentStatus.RUNNING
        
        start_time = time.time()
        
        try:
            # Execute the operation
            result = operation_func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Update metrics
            self.metrics.update_metrics(True, execution_time)
            self.status = AgentStatus.SUCCESS
            
            self.logger.info(f"Completed {operation_name} in {execution_time:.2f}s")
            
            # Return result wrapped in BaseResult if it's not already
            if isinstance(result, BaseResult):
                result.execution_time = execution_time
                return result
            else:
                return BaseResult(
                    success=True,
                    status=AgentStatus.SUCCESS,
                    message=f"{operation_name} completed successfully",
                    data=result,
                    execution_time=execution_time
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # Update metrics
            self.metrics.update_metrics(False, execution_time)
            self.status = AgentStatus.ERROR
            
            self.logger.error(f"Failed {operation_name} after {execution_time:.2f}s: {error_msg}")
            
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=error_msg,
                message=f"{operation_name} failed",
                execution_time=execution_time
            )
    
    def validate_input(self, data: Any, expected_type: type = None) -> bool:
        """Validate input data.
        
        Args:
            data: Data to validate
            expected_type: Expected type for the data
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        if not self.validate_inputs:
            return True
        
        if expected_type and not isinstance(data, expected_type):
            raise ValueError(f"Expected {expected_type.__name__}, got {type(data).__name__}")
        
        if data is None:
            raise ValueError("Input data cannot be None")
        
        return True
    
    def validate_output(self, data: Any, expected_type: type = None) -> bool:
        """Validate output data.
        
        Args:
            data: Data to validate
            expected_type: Expected type for the data
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        if not self.validate_outputs:
            return True
        
        if expected_type and not isinstance(data, expected_type):
            raise ValueError(f"Output validation failed: Expected {expected_type.__name__}, got {type(data).__name__}")
        
        return True
    
    def get_metrics(self) -> AgentMetrics:
        """Get current agent metrics."""
        return self.metrics
    
    def reset_metrics(self):
        """Reset agent metrics."""
        self.metrics = AgentMetrics()
        self.logger.info("Agent metrics reset")
    
    def get_status(self) -> AgentStatus:
        """Get current agent status."""
        return self.status
    
    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.config.copy()
    
    def update_config(self, **kwargs):
        """Update agent configuration."""
        self.config.update(kwargs)
        self.logger.info(f"Updated configuration: {list(kwargs.keys())}")
    
    # Abstract methods that subclasses must implement
    
    @abstractmethod
    def process(self, *args, **kwargs) -> BaseResult:
        """Main processing method that each agent must implement.
        
        This should be the primary entry point for the agent's functionality.
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate the agent's configuration.
        
        Returns:
            True if configuration is valid, raises ValueError if invalid
        """
        pass
    
    # Optional methods that subclasses can override
    
    def cleanup(self):
        """Cleanup resources when agent is done.
        
        Subclasses can override this to clean up any resources.
        """
        self.logger.info(f"Cleaning up {self.name}")
        self.status = AgentStatus.IDLE
    
    def health_check(self) -> BaseResult:
        """Perform a health check of the agent.
        
        Returns:
            BaseResult indicating agent health
        """
        try:
            # Basic health checks
            config_valid = self.validate_configuration()
            
            return BaseResult(
                success=True,
                status=AgentStatus.SUCCESS,
                message=f"{self.name} is healthy",
                data={
                    "config_valid": config_valid,
                    "metrics": self.metrics.model_dump(),
                    "status": self.status.value
                }
            )
        except Exception as e:
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message=f"{self.name} health check failed"
            )
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.status.value})"


# Utility functions for working with agents

def create_agent_result(success: bool, data: Any = None, message: str = None, 
                       error: str = None, **metadata) -> BaseResult:
    """Utility function to create standardized agent results."""
    status = AgentStatus.SUCCESS if success else AgentStatus.ERROR
    
    return BaseResult(
        success=success,
        status=status,
        data=data,
        message=message,
        error=error,
        metadata=metadata
    )


def batch_process_agents(agents: List[BaseAgent], operation: str, *args, **kwargs) -> List[BaseResult]:
    """Process multiple agents with the same operation.
    
    Args:
        agents: List of agents to process
        operation: Name of the operation method to call
        *args: Arguments to pass to the operation
        **kwargs: Keyword arguments to pass to the operation
        
    Returns:
        List of BaseResult objects from each agent
    """
    results = []
    
    for agent in agents:
        try:
            if hasattr(agent, operation):
                method = getattr(agent, operation)
                result = method(*args, **kwargs)
                results.append(result)
            else:
                results.append(BaseResult(
                    success=False,
                    status=AgentStatus.ERROR,
                    error=f"Agent {agent.name} does not support operation '{operation}'"
                ))
        except Exception as e:
            results.append(BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message=f"Failed to execute {operation} on {agent.name}"
            ))
    
    return results
