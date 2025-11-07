"""Parser for Windows dump files (.dmp)."""

import os
from datetime import datetime

from minidump.minidumpfile import MinidumpFile

from src.models.dump_analysis import DumpFileAnalysis


class DumpParserError(Exception):
    """Exception raised when dump file parsing fails."""
    pass


class DumpParser:
    """Parser for Windows memory dump files.
    
    This class uses the minidump library to extract crash information
    from Windows dump files (.dmp format).
    """

    def parse(self, file_path: str) -> DumpFileAnalysis:
        """Parse a dump file and extract crash information.
        
        Args:
            file_path: Path to the .dmp file
            
        Returns:
            DumpFileAnalysis object containing extracted information
            
        Raises:
            DumpParserError: If file cannot be parsed
            FileNotFoundError: If file does not exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dump file not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise DumpParserError(f"Dump file is empty: {file_path}")
        
        parsing_errors = []
        
        try:
            mf = MinidumpFile.parse(file_path)
            
            sysinfo = mf.sysinfo
            os_version = self._extract_os_version(sysinfo)
            architecture = self._extract_architecture(sysinfo)
            
            exception_info = None
            crash_type = "UNKNOWN"
            error_code = None
            faulting_address = None
            thread_id = None
            
            if mf.exception:
                exception_info = mf.exception
                crash_type = "EXCEPTION"
                if hasattr(exception_info, 'ExceptionRecord') and exception_info.ExceptionRecord:
                    error_code = f"0x{exception_info.ExceptionRecord.ExceptionCode:08X}"
                    if hasattr(exception_info.ExceptionRecord, 'ExceptionAddress'):
                        faulting_address = f"0x{exception_info.ExceptionRecord.ExceptionAddress:016X}"
                if hasattr(exception_info, 'ThreadId'):
                    thread_id = exception_info.ThreadId
            
            process_name = "Unknown"
            process_id = None
            
            if mf.modules and mf.modules.modules:
                first_module = mf.modules.modules[0]
                if hasattr(first_module, 'name'):
                    process_name = os.path.basename(first_module.name)
            
            crash_timestamp = datetime.utcnow()  # Default to now
            if hasattr(mf, 'header') and hasattr(mf.header, 'TimeDateStamp'):
                try:
                    crash_timestamp = datetime.fromtimestamp(mf.header.TimeDateStamp)
                except (ValueError, OSError) as e:
                    parsing_errors.append(f"Could not parse timestamp: {e}")
            
            faulting_module = None
            if exception_info and hasattr(exception_info, 'ExceptionRecord'):
                exc_addr = getattr(exception_info.ExceptionRecord, 'ExceptionAddress', None)
                if exc_addr and mf.modules:
                    faulting_module = self._find_module_at_address(mf.modules, exc_addr)
            
            stack_trace = []
            if mf.threads:
                try:
                    target_thread = None
                    if thread_id is not None:
                        for thread in mf.threads.threads:
                            if hasattr(thread, 'ThreadId') and thread.ThreadId == thread_id:
                                target_thread = thread
                                break
                    
                    if target_thread is None and mf.threads.threads:
                        target_thread = mf.threads.threads[0]
                    
                    if target_thread and hasattr(target_thread, 'Stack'):
                        stack_trace = self._extract_stack_trace(target_thread, mf.modules)
                except Exception as e:
                    parsing_errors.append(f"Error extracting stack trace: {e}")
            
            loaded_modules = []
            if mf.modules and mf.modules.modules:
                for module in mf.modules.modules[:50]:  # Limit to first 50 modules
                    if hasattr(module, 'name'):
                        module_name = os.path.basename(module.name)
                        loaded_modules.append(module_name)
            
            system_uptime = None
            if hasattr(sysinfo, 'ProcessorArchitecture'):
                pass
            
            return DumpFileAnalysis(
                file_path=file_path,
                file_size_bytes=file_size,
                crash_timestamp=crash_timestamp,
                crash_type=crash_type,
                process_name=process_name,
                os_version=os_version,
                architecture=architecture,
                error_code=error_code,
                faulting_module=faulting_module,
                faulting_address=faulting_address,
                process_id=process_id,
                thread_id=thread_id,
                stack_trace=stack_trace,
                loaded_modules=loaded_modules,
                system_uptime_seconds=system_uptime,
                parsing_errors=parsing_errors
            )
            
        except Exception as e:
            raise DumpParserError(f"Failed to parse dump file: {e}") from e

    def _extract_os_version(self, sysinfo) -> str:
        """Extract OS version from system info."""
        try:
            if hasattr(sysinfo, 'BuildNumber'):
                build = sysinfo.BuildNumber
                major = getattr(sysinfo, 'MajorVersion', 0)
                minor = getattr(sysinfo, 'MinorVersion', 0)
                
                if major == 10 and minor == 0:
                    return f"Windows 10/11 Build {build}"
                elif major == 6 and minor == 3:
                    return f"Windows 8.1 Build {build}"
                elif major == 6 and minor == 2:
                    return f"Windows 8 Build {build}"
                elif major == 6 and minor == 1:
                    return f"Windows 7 Build {build}"
                else:
                    return f"Windows {major}.{minor} Build {build}"
            return "Windows (version unknown)"
        except Exception:
            return "Windows (version unknown)"

    def _extract_architecture(self, sysinfo) -> str:
        """Extract system architecture from system info."""
        try:
            if hasattr(sysinfo, 'ProcessorArchitecture'):
                arch = sysinfo.ProcessorArchitecture
                if arch == 9:  # PROCESSOR_ARCHITECTURE_AMD64
                    return "x64"
                elif arch == 0:  # PROCESSOR_ARCHITECTURE_INTEL
                    return "x86"
                elif arch == 5:  # PROCESSOR_ARCHITECTURE_ARM
                    return "ARM"
                elif arch == 12:  # PROCESSOR_ARCHITECTURE_ARM64
                    return "ARM64"
            return "x64"  # Default assumption
        except Exception:
            return "x64"

    def _find_module_at_address(self, modules, address: int) -> str | None:
        """Find the module that contains the given address."""
        try:
            for module in modules.modules:
                if hasattr(module, 'BaseOfImage') and hasattr(module, 'SizeOfImage'):
                    base = module.BaseOfImage
                    size = module.SizeOfImage
                    if base <= address < base + size:
                        return os.path.basename(module.name) if hasattr(module, 'name') else None
        except Exception:
            pass
        return None

    def _extract_stack_trace(self, thread, modules, max_frames: int = 20) -> list[str]:
        """Extract stack trace from thread."""
        stack_trace = []
        try:
            if hasattr(thread, 'Stack') and thread.Stack:
                stack = thread.Stack
                if hasattr(stack, 'memory') and stack.memory:
                    stack_trace.append(f"Stack memory region: 0x{stack.memory.start_virtual_address:016X}")
                    stack_trace.append(f"Stack size: {len(stack.memory.data)} bytes")
        except Exception:
            pass
        
        if not stack_trace:
            stack_trace.append("Stack trace requires symbol files for detailed analysis")
        
        return stack_trace[:max_frames]
